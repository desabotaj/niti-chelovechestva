"""Export aggregated parquet → frontend-friendly JSON (one file per decade).

Writes everything under `frontend/public/data/`. Files are kept small
(<2 MB each) so the front-end can stream-load decades on demand while
the time-slider scrubs.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

import duckdb

from generator import geography
from generator.config import (
    ARCS_PATH,
    DECADES,
    FRONTEND_DATA,
    HEX_AGG_PATH,
    LINEAGES_PATH,
    N_DECADES,
    ensure_dirs,
)
from generator.events import event_window_summary, load_events


def _connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    return con


def _clean_existing(suffix: str) -> None:
    for f in FRONTEND_DATA.glob(suffix):
        f.unlink()


def export_meta() -> None:
    print("[export] writing meta.json …")
    events = load_events()
    meta = {
        "version": 1,
        "startYear": int(DECADES[0]),
        "endYear": int(DECADES[-1]) + 10,
        "decades": [int(y) for y in DECADES],
        "decadeCount": N_DECADES,
        "regions": [
            {
                "id": r.id,
                "name": r.name,
                "lat": r.lat,
                "lon": r.lon,
                "continent": r.continent,
            }
            for r in geography.REGIONS
        ],
        "ethnoGroups": list(geography.ETHNO_GROUPS),
        "events": [
            {
                "id": e.id,
                "name": e.name,
                "start": e.start,
                "end": e.end,
                "type": e.type,
                "regions": list(e.regions),
            }
            for e in events
        ],
    }
    (FRONTEND_DATA / "meta.json").write_text(
        json.dumps(meta, separators=(",", ":")), encoding="utf-8"
    )


def export_hex(con: duckdb.DuckDBPyConnection) -> None:
    print("[export] writing hex_*.json files …")
    if not HEX_AGG_PATH.exists():
        print("[export] hex_agg.parquet missing, skipped")
        return
    _clean_existing("hex_*.json")

    df = con.execute(
        f"""
        SELECT decade_idx, h3, pop, dominant_continent
        FROM read_parquet('{HEX_AGG_PATH.as_posix()}')
        ORDER BY decade_idx, pop DESC
        """
    ).fetchdf()

    for d, group in df.groupby("decade_idx"):
        cells = [
            {"h": str(row.h3), "p": int(row.pop), "c": str(row.dominant_continent)}
            for row in group.itertuples(index=False)
        ]
        (FRONTEND_DATA / f"hex_{int(d):02d}.json").write_text(
            json.dumps({"d": int(d), "cells": cells}, separators=(",", ":")),
            encoding="utf-8",
        )
    print(f"[export]   {df.shape[0]:,} hex rows across {df['decade_idx'].nunique()} decades")


def export_arcs(con: duckdb.DuckDBPyConnection) -> None:
    print("[export] writing arcs_*.json files …")
    if not ARCS_PATH.exists():
        print("[export] arcs.parquet missing, skipped")
        return
    _clean_existing("arcs_*.json")

    df = con.execute(
        f"""
        SELECT decade_idx, decade_year,
               src_id, src_name, src_lat, src_lon, src_continent,
               dst_id, dst_name, dst_lat, dst_lon, dst_continent,
               migrations, top_cause
        FROM read_parquet('{ARCS_PATH.as_posix()}')
        ORDER BY decade_idx, migrations DESC
        """
    ).fetchdf()

    for d, group in df.groupby("decade_idx"):
        arcs = []
        for row in group.itertuples(index=False):
            arcs.append({
                "from": {"id": str(row.src_id), "name": str(row.src_name),
                         "lat": float(row.src_lat), "lon": float(row.src_lon),
                         "cont": str(row.src_continent)},
                "to":   {"id": str(row.dst_id), "name": str(row.dst_name),
                         "lat": float(row.dst_lat), "lon": float(row.dst_lon),
                         "cont": str(row.dst_continent)},
                "n":    int(row.migrations),
                "cause": str(row.top_cause),
            })
        (FRONTEND_DATA / f"arcs_{int(d):02d}.json").write_text(
            json.dumps({"d": int(d), "year": int(group['decade_year'].iloc[0]),
                        "arcs": arcs}, separators=(",", ":")),
            encoding="utf-8",
        )
    print(f"[export]   {df.shape[0]:,} arcs across {df['decade_idx'].nunique()} decades")


def export_lineages(con: duckdb.DuckDBPyConnection) -> None:
    print("[export] writing lineages.json …")
    if not LINEAGES_PATH.exists():
        print("[export] lineages.parquet missing, skipped")
        return
    df = con.execute(
        f"""
        SELECT lineage_id, depth, person_id, year, region_idx, region_id,
               region_name, continent, lat, lon
        FROM read_parquet('{LINEAGES_PATH.as_posix()}')
        ORDER BY lineage_id, depth
        """
    ).fetchdf()

    lineages = []
    for lid, group in df.groupby("lineage_id"):
        nodes = [
            {
                "d": int(row.depth),
                "y": int(row.year),
                "r": str(row.region_id),
                "n": str(row.region_name),
                "c": str(row.continent),
                "lat": float(row.lat),
                "lon": float(row.lon),
            }
            for row in group.itertuples(index=False)
        ]
        if len(nodes) < 2:
            continue
        starts = nodes[-1]["n"]
        ends = nodes[0]["n"]
        title = f"{starts} → {ends}"
        lineages.append({
            "id": int(lid),
            "title": title,
            "span": [nodes[-1]["y"], nodes[0]["y"]],
            "nodes": nodes,
        })

    (FRONTEND_DATA / "lineages.json").write_text(
        json.dumps({"lineages": lineages}, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"[export]   {len(lineages)} lineages exported")


def export_event_timeline() -> None:
    print("[export] writing events_timeline.json …")
    events = load_events()
    summary = event_window_summary(events)
    yearly = [
        {"year": y, "names": summary.get(y, [])}
        for y in range(int(DECADES[0]), int(DECADES[-1]) + 11)
    ]
    (FRONTEND_DATA / "events_timeline.json").write_text(
        json.dumps({"yearly": yearly}, separators=(",", ":")),
        encoding="utf-8",
    )


def run() -> None:
    ensure_dirs()
    t0 = time.time()
    con = _connect()
    try:
        export_meta()
        export_hex(con)
        export_arcs(con)
        export_lineages(con)
        export_event_timeline()
    finally:
        con.close()
    print(f"[export] done in {time.time() - t0:.1f}s")
    print(f"[export] output: {FRONTEND_DATA.resolve()}")


if __name__ == "__main__":
    run()
