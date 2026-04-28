"""DuckDB + H3 aggregation: turn raw Parquet into frontend-ready tiles.

Outputs:

    backend/data/hex_agg.parquet      — per (decade, h3 res=3) population
                                        density + dominant continent
    backend/data/arcs.parquet         — per (decade, src_region, dst_region)
                                        migration counts + cause labels
    backend/data/lineages.parquet     — sampled multi-generation lineages
                                        for the drill-in feature

The H3 community extension is loaded lazily so first run downloads it.
"""

from __future__ import annotations

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
    HEX_AGG_PATH,
    INDIVIDUALS_PATH,
    LINEAGES_PATH,
    MIGRATIONS_PATH,
    ensure_dirs,
)

H3_RES = 3
TOP_ARCS_PER_DECADE = 250


def _connect() -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(":memory:")
    con.execute("SET memory_limit='4GB'")
    con.execute("INSTALL h3 FROM community")
    con.execute("LOAD h3")
    return con


def _ensure_inputs() -> None:
    if not INDIVIDUALS_PATH.exists():
        raise FileNotFoundError(
            f"Individuals parquet not found at {INDIVIDUALS_PATH}. "
            "Run `python -m pipeline.spark_generate` first."
        )
    if not MIGRATIONS_PATH.exists():
        raise FileNotFoundError(
            f"Migrations parquet not found at {MIGRATIONS_PATH}. "
            "Run `python -m pipeline.spark_generate` first."
        )


def _build_regions_table(con: duckdb.DuckDBPyConnection) -> None:
    rows = [
        (i, r.id, r.name, r.lat, r.lon, r.continent, ETHNO_DOMINANT(r.ethno))
        for i, r in enumerate(geography.REGIONS)
    ]
    con.executemany(
        "INSERT INTO regions VALUES (?, ?, ?, ?, ?, ?, ?)",
        rows,
    )


def ETHNO_DOMINANT(vec: tuple[float, ...]) -> str:
    return geography.ETHNO_GROUPS[max(range(len(vec)), key=lambda i: vec[i])]


def _setup_regions_view(con: duckdb.DuckDBPyConnection) -> None:
    con.execute(
        """
        CREATE TABLE regions (
          region_idx INTEGER,
          region_id  VARCHAR,
          name       VARCHAR,
          lat        DOUBLE,
          lon        DOUBLE,
          continent  VARCHAR,
          ethno      VARCHAR
        )
        """
    )
    _build_regions_table(con)
    decade_rows = [(i, int(y)) for i, y in enumerate(DECADES)]
    con.execute("CREATE TABLE decades (decade_idx INTEGER, decade_year INTEGER)")
    con.executemany("INSERT INTO decades VALUES (?, ?)", decade_rows)


def aggregate_hex(con: duckdb.DuckDBPyConnection) -> None:
    print("[aggregate] computing hex population density…")
    HEX_AGG_PATH.parent.mkdir(parents=True, exist_ok=True)
    sql = f"""
    COPY (
        WITH living AS (
            SELECT
                i.decade_idx,
                d.decade_year,
                r.continent,
                h3_latlng_to_cell(i.birth_lat, i.birth_lon, {H3_RES}) AS h3_cell
            FROM read_parquet(
                '{INDIVIDUALS_PATH.as_posix()}/**/*.parquet',
                hive_partitioning = 1
            ) i
            JOIN decades  d ON d.decade_idx  = i.decade_idx
            JOIN regions  r ON r.region_idx  = i.birth_region_idx
            WHERE i.death_year >= d.decade_year
              AND i.birth_year <= d.decade_year + 9
        ),
        cont_counts AS (
            SELECT decade_idx, h3_cell, continent, COUNT(*) AS cont_count
            FROM living
            GROUP BY 1, 2, 3
        ),
        cell_totals AS (
            SELECT decade_idx, h3_cell, SUM(cont_count) AS pop
            FROM cont_counts
            GROUP BY 1, 2
        ),
        dominant AS (
            SELECT decade_idx, h3_cell,
                   arg_max(continent, cont_count) AS dominant_continent
            FROM cont_counts
            GROUP BY 1, 2
        )
        SELECT
            ct.decade_idx,
            d.decade_year,
            h3_h3_to_string(ct.h3_cell) AS h3,
            CAST(ct.pop AS BIGINT)      AS pop,
            dom.dominant_continent
        FROM cell_totals ct
        JOIN dominant dom
          ON dom.decade_idx = ct.decade_idx
         AND dom.h3_cell    = ct.h3_cell
        JOIN decades d
          ON d.decade_idx = ct.decade_idx
        ORDER BY ct.decade_idx, ct.pop DESC
    ) TO '{HEX_AGG_PATH.as_posix()}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE 1)
    """
    con.execute(sql)
    n_rows = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{HEX_AGG_PATH.as_posix()}')"
    ).fetchone()[0]
    print(f"[aggregate] hex_agg rows: {n_rows:,}")


def aggregate_arcs(con: duckdb.DuckDBPyConnection) -> None:
    print("[aggregate] computing top migration arcs per decade…")
    ARCS_PATH.parent.mkdir(parents=True, exist_ok=True)
    sql = f"""
    COPY (
        WITH cause_counts AS (
            SELECT decade_idx, from_region_idx, to_region_idx, cause_label,
                   COUNT(*) AS cnt
            FROM read_parquet(
                '{MIGRATIONS_PATH.as_posix()}/**/*.parquet',
                hive_partitioning = 1
            )
            GROUP BY 1, 2, 3, 4
        ),
        totals AS (
            SELECT decade_idx, from_region_idx, to_region_idx,
                   SUM(cnt) AS migrations,
                   arg_max(cause_label, cnt) AS top_cause
            FROM cause_counts
            GROUP BY 1, 2, 3
        ),
        ranked AS (
            SELECT t.*,
                   ROW_NUMBER() OVER (
                     PARTITION BY decade_idx
                     ORDER BY migrations DESC
                   ) AS rk
            FROM totals t
        )
        SELECT
            r.decade_idx,
            d.decade_year,
            rs.region_id AS src_id, rs.name AS src_name,
            rs.lat       AS src_lat, rs.lon AS src_lon,
            rs.continent AS src_continent,
            rd.region_id AS dst_id, rd.name AS dst_name,
            rd.lat       AS dst_lat, rd.lon AS dst_lon,
            rd.continent AS dst_continent,
            CAST(r.migrations AS BIGINT) AS migrations,
            r.top_cause
        FROM ranked r
        JOIN regions rs ON rs.region_idx = r.from_region_idx
        JOIN regions rd ON rd.region_idx = r.to_region_idx
        JOIN decades d  ON d.decade_idx  = r.decade_idx
        WHERE r.rk <= {TOP_ARCS_PER_DECADE}
        ORDER BY r.decade_idx, r.migrations DESC
    ) TO '{ARCS_PATH.as_posix()}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE 1)
    """
    con.execute(sql)
    n_rows = con.execute(
        f"SELECT COUNT(*) FROM read_parquet('{ARCS_PATH.as_posix()}')"
    ).fetchone()[0]
    print(f"[aggregate] arcs rows: {n_rows:,}")


def sample_lineages(con: duckdb.DuckDBPyConnection, n_samples: int = 50, generations: int = 14) -> None:
    """Walk synthetic parent_id back from random late-era individuals to seed the drill-in panel."""
    print(f"[aggregate] sampling {n_samples} 'star lineages' over {generations} generations…")
    LINEAGES_PATH.parent.mkdir(parents=True, exist_ok=True)

    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE individuals_idx AS
        SELECT id, birth_year, birth_region_idx, birth_lat, birth_lon, parent1_id, decade_idx
        FROM read_parquet(
            '{INDIVIDUALS_PATH.as_posix()}/**/*.parquet',
            hive_partitioning = 1
        )
        """
    )

    seeds = con.execute(
        f"""
        SELECT id, birth_year, birth_region_idx, birth_lat, birth_lon, parent1_id
        FROM (
            SELECT id, birth_year, birth_region_idx, birth_lat, birth_lon, parent1_id
            FROM individuals_idx
            WHERE decade_idx >= 45
        ) t
        ORDER BY hash(id)
        LIMIT {n_samples}
        """
    ).fetchdf()

    if seeds.empty:
        print("[aggregate] no seeds found, lineage sampling skipped")
        return

    individuals_lookup = {
        row.id: (row.birth_year, row.birth_region_idx, row.birth_lat, row.birth_lon, row.parent1_id)
        for row in con.execute(
            "SELECT id, birth_year, birth_region_idx, birth_lat, birth_lon, parent1_id FROM individuals_idx"
        ).fetchdf().itertuples(index=False)
    }

    rows: list[tuple] = []
    for lineage_id, seed in enumerate(seeds.itertuples(index=False)):
        current_id = int(seed.id)
        depth = 0
        rows.append((lineage_id, depth, current_id, int(seed.birth_year),
                     int(seed.birth_region_idx), float(seed.birth_lat), float(seed.birth_lon)))
        while depth < generations - 1:
            entry = individuals_lookup.get(current_id)
            if entry is None:
                break
            parent = entry[4]
            if parent is None or int(parent) == -1:
                break
            current_id = int(parent)
            parent_entry = individuals_lookup.get(current_id)
            if parent_entry is None:
                break
            depth += 1
            rows.append((lineage_id, depth, current_id, int(parent_entry[0]),
                         int(parent_entry[1]), float(parent_entry[2]), float(parent_entry[3])))

    if not rows:
        print("[aggregate] lineage walk produced no rows")
        return

    con.execute("DROP TABLE IF EXISTS lineage_tmp")
    con.execute(
        """
        CREATE TABLE lineage_tmp(
            lineage_id INTEGER,
            depth      INTEGER,
            person_id  BIGINT,
            year       INTEGER,
            region_idx INTEGER,
            lat        DOUBLE,
            lon        DOUBLE
        )
        """
    )
    con.executemany("INSERT INTO lineage_tmp VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    con.execute(
        f"""
        COPY (
            SELECT l.lineage_id, l.depth, l.person_id, l.year,
                   l.region_idx, r.region_id, r.name AS region_name, r.continent,
                   l.lat, l.lon
            FROM lineage_tmp l
            JOIN regions r ON r.region_idx = l.region_idx
            ORDER BY l.lineage_id, l.depth
        ) TO '{LINEAGES_PATH.as_posix()}' (FORMAT PARQUET, OVERWRITE_OR_IGNORE 1)
        """
    )
    print(f"[aggregate] lineages rows: {len(rows):,}")


def run() -> None:
    ensure_dirs()
    _ensure_inputs()
    t0 = time.time()
    con = _connect()
    try:
        _setup_regions_view(con)
        aggregate_hex(con)
        aggregate_arcs(con)
        sample_lineages(con)
    finally:
        con.close()
    print(f"[aggregate] done in {time.time() - t0:.1f}s")


if __name__ == "__main__":
    run()
