"""Single-process generator that mirrors the Spark pipeline.

Useful when:

  * PySpark / Java toolchain are unavailable on the host machine,
  * iterating on the model at `tiny` / `small` scale,
  * sanity-checking the output before launching a cluster job.

Outputs are byte-for-byte compatible Parquet datasets readable by the
downstream `aggregate.py` step.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from generator import geography
from generator.config import (
    GLOBAL_SEED,
    INDIVIDUALS_PATH,
    MIGRATIONS_PATH,
    N_DECADES,
    SCALES,
    ensure_dirs,
)
from generator.events import load_events
from generator.genealogy import cohort_plan_from_weights
from generator.migration import cause_index, flow_cube
from generator.population import normalised_birth_weights, population_trajectory
from generator.spawn import make_context, spawn_cohort, spawn_migration_batch


def _write_partitioned(df: pd.DataFrame, root: Path, partition_col: str) -> None:
    if df.empty:
        return
    root.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_to_dataset(
        table,
        root_path=str(root),
        partition_cols=[partition_col],
        existing_data_behavior="overwrite_or_ignore",
        compression="snappy",
    )


def _wipe(path: Path) -> None:
    if not path.exists():
        return
    for child in sorted(path.glob("**/*"), reverse=True):
        try:
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        except OSError:
            pass
    try:
        path.rmdir()
    except OSError:
        pass


def run(scale_name: str = "small", seed: int | None = None) -> None:
    if seed is not None:
        np.random.seed(seed)

    scale = SCALES[scale_name]
    print(f"[local-generate] scale={scale.name} ({scale.description})")
    ensure_dirs()

    events = load_events()
    print(f"[local-generate] loaded {len(events)} historical events")

    pop = population_trajectory(events, total_world_1525=1.0)
    weights = normalised_birth_weights(pop, events)

    individuals_target = max(scale.initial_population * 30, 50_000)
    migrations_target = max(scale.initial_population * 20, 30_000)

    plan = cohort_plan_from_weights(weights, individuals_target)
    cube = flow_cube(events, pop)
    flows_per_decade = (cube * migrations_target).astype(np.int64)
    cause_to_id = cause_index(events)
    ctx = make_context(plan, cause_to_id)

    print(f"[local-generate] cohort total individuals: {plan.total():,}")
    print(f"[local-generate] migrations target:       {int(flows_per_decade.sum()):,}")
    print(f"[local-generate] global seed: {GLOBAL_SEED}")

    t0 = time.time()

    _wipe(INDIVIDUALS_PATH)
    print(f"[local-generate] writing {INDIVIDUALS_PATH} …")
    n_regions = geography.N_REGIONS
    for decade_idx in range(N_DECADES):
        frames = []
        for region_idx in range(n_regions):
            n = plan.cohort_size(decade_idx, region_idx)
            if n > 0:
                frames.append(spawn_cohort(decade_idx, region_idx, n, ctx))
        if not frames:
            continue
        df = pd.concat(frames, ignore_index=True)
        _write_partitioned(df, INDIVIDUALS_PATH, "decade_idx")
        print(f"[local-generate]   decade {decade_idx:>2} / {N_DECADES} → {len(df):>10,} rows")

    _wipe(MIGRATIONS_PATH)
    print(f"[local-generate] writing {MIGRATIONS_PATH} …")
    for decade_idx in range(N_DECADES):
        slice_ = flows_per_decade[decade_idx]
        idxs = np.argwhere(slice_ > 0)
        if len(idxs) == 0:
            continue
        frames = []
        for src, dst in idxs:
            n = int(slice_[src, dst])
            frames.append(spawn_migration_batch(decade_idx, int(src), int(dst), n, events, ctx))
        if not frames:
            continue
        df = pd.concat(frames, ignore_index=True)
        _write_partitioned(df, MIGRATIONS_PATH, "decade_idx")
        print(f"[local-generate]   decade {decade_idx:>2} / {N_DECADES} → {len(df):>10,} migrations")

    elapsed = time.time() - t0
    print(f"[local-generate] done in {elapsed:.1f}s")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scale", default="small", choices=list(SCALES.keys()),
                   help="Scale preset (default: small).")
    p.add_argument("--seed", type=int, default=None, help="Override the global seed.")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    run(scale_name=args.scale, seed=args.seed)
