"""Generate the Threads of Humanity dataset on a Spark cluster.

Run end-to-end:

    python -m pipeline.spark_generate --scale small

The generator is *embarrassingly parallel*: each (decade, region) cohort
becomes a Spark partition, individuals & migrations are produced inside
`applyInPandas` by vectorised NumPy calls. The output is two
decade-partitioned Parquet datasets:

    backend/data/individuals.parquet/decade_idx=NN/...
    backend/data/migrations.parquet/decade_idx=NN/...

For laptops without a working PySpark / Java toolchain, see the matching
single-process generator in `pipeline.local_generate` — same data, same
schema, no JVM.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from generator import geography
from generator.config import (
    DECADES,
    GLOBAL_SEED,
    INDIVIDUALS_PATH,
    MIGRATIONS_PATH,
    N_DECADES,
    SCALES,
    ScalePreset,
    ensure_dirs,
)
from generator.events import load_events
from generator.genealogy import cohort_plan_from_weights
from generator.migration import cause_index, flow_cube
from generator.population import normalised_birth_weights, population_trajectory
from generator.spawn import make_context, spawn_cohort, spawn_migration_batch


def _make_spark(scale: ScalePreset):
    if sys.platform.startswith("win") and "PYSPARK_PYTHON" not in os.environ:
        os.environ["PYSPARK_PYTHON"] = sys.executable
    from pyspark.sql import SparkSession

    builder = (
        SparkSession.builder.appName(f"threads-of-humanity-{scale.name}")
        .master("local[*]")
        .config("spark.sql.shuffle.partitions", str(scale.spark_partitions))
        .config("spark.sql.execution.arrow.pyspark.enabled", "true")
        .config("spark.driver.memory", "4g")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.ui.showConsoleProgress", "false")
        .config("spark.sql.adaptive.enabled", "true")
    )
    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("WARN")
    return spark


def _individual_schema():
    from pyspark.sql.types import (
        ByteType,
        FloatType,
        IntegerType,
        LongType,
        ShortType,
        StringType,
        StructField,
        StructType,
    )

    return StructType(
        [
            StructField("id", LongType(), False),
            StructField("birth_year", ShortType(), False),
            StructField("death_year", ShortType(), False),
            StructField("birth_region_idx", ByteType(), False),
            StructField("birth_lat", FloatType(), False),
            StructField("birth_lon", FloatType(), False),
            StructField("sex", ByteType(), False),
            StructField("parent1_id", LongType(), True),
            StructField("parent2_id", LongType(), True),
            StructField("birth_continent", StringType(), False),
            StructField("decade_idx", IntegerType(), False),
        ]
    )


def _migration_schema():
    from pyspark.sql.types import (
        ByteType,
        FloatType,
        IntegerType,
        LongType,
        ShortType,
        StringType,
        StructField,
        StructType,
    )

    return StructType(
        [
            StructField("person_id", LongType(), False),
            StructField("year", ShortType(), False),
            StructField("from_region_idx", ByteType(), False),
            StructField("to_region_idx", ByteType(), False),
            StructField("from_lat", FloatType(), False),
            StructField("from_lon", FloatType(), False),
            StructField("to_lat", FloatType(), False),
            StructField("to_lon", FloatType(), False),
            StructField("cause_id", IntegerType(), False),
            StructField("cause_label", StringType(), False),
            StructField("decade_idx", IntegerType(), False),
        ]
    )


def _cohort_apply_factory(ctx_payload: dict):
    """Return a closure suitable for Spark's `applyInPandas`."""
    from generator.spawn import SpawnContext
    from generator.genealogy import CohortPlan

    def _build_ctx() -> SpawnContext:
        return SpawnContext(
            cohort_plan=CohortPlan(counts=ctx_payload["cohort_counts"]),
            distance_km=ctx_payload["distance_km"],
            region_centers=ctx_payload["region_centers"],
            region_radii=ctx_payload["region_radii"],
            region_continents=ctx_payload["region_continents"],
            cause_to_id=ctx_payload["cause_to_id"],
        )

    def fn(pdf: pd.DataFrame) -> pd.DataFrame:
        if pdf.empty:
            return pd.DataFrame()
        decade_idx = int(pdf["decade_idx"].iloc[0])
        region_idx = int(pdf["region_idx"].iloc[0])
        n = int(pdf["cohort_count"].iloc[0])
        return spawn_cohort(decade_idx, region_idx, n, _build_ctx())

    return fn


def _migration_apply_factory(ctx_payload: dict, events_payload: list):
    from generator.spawn import SpawnContext
    from generator.genealogy import CohortPlan
    from generator.events import Event, Pull

    def _build_ctx() -> SpawnContext:
        return SpawnContext(
            cohort_plan=CohortPlan(counts=ctx_payload["cohort_counts"]),
            distance_km=ctx_payload["distance_km"],
            region_centers=ctx_payload["region_centers"],
            region_radii=ctx_payload["region_radii"],
            region_continents=ctx_payload["region_continents"],
            cause_to_id=ctx_payload["cause_to_id"],
        )

    def _build_events() -> list[Event]:
        out: list[Event] = []
        for e in events_payload:
            pulls = tuple(Pull(p["src"], p["dst"], p["weight"], p.get("reason", ""))
                          for p in e.get("pulls", []) or [])
            out.append(Event(
                id=e["id"], name=e["name"], start=e["start"], end=e["end"], type=e["type"],
                mortality=e.get("mortality", 1.0), birth=e.get("birth", 1.0),
                regions=tuple(e.get("regions", []) or []), pulls=pulls,
            ))
        return out

    def fn(pdf: pd.DataFrame) -> pd.DataFrame:
        if pdf.empty:
            return pd.DataFrame()
        decade_idx = int(pdf["decade_idx"].iloc[0])
        src = int(pdf["from_region_idx"].iloc[0])
        dst = int(pdf["to_region_idx"].iloc[0])
        n = int(pdf["mig_count"].iloc[0])
        return spawn_migration_batch(decade_idx, src, dst, n, _build_events(), _build_ctx())

    return fn


def _events_payload(events) -> list[dict]:
    return [
        {
            "id": e.id,
            "name": e.name,
            "start": e.start,
            "end": e.end,
            "type": e.type,
            "mortality": e.mortality,
            "birth": e.birth,
            "regions": list(e.regions),
            "pulls": [{"src": p.src, "dst": p.dst, "weight": p.weight, "reason": p.reason}
                       for p in e.pulls],
        }
        for e in events
    ]


def run(scale_name: str = "small", seed: int | None = None) -> None:
    scale = SCALES[scale_name]
    print(f"[spark-generate] scale={scale.name} ({scale.description})")
    ensure_dirs()

    events = load_events()
    print(f"[spark-generate] loaded {len(events)} historical events")

    pop = population_trajectory(events, total_world_1525=1.0)
    weights = normalised_birth_weights(pop, events)

    individuals_target = max(scale.initial_population * 30, 50_000)
    migrations_target = max(scale.initial_population * 20, 30_000)

    plan = cohort_plan_from_weights(weights, individuals_target)
    cube = flow_cube(events, pop)
    flows_per_decade = (cube * migrations_target).astype(np.int64)
    cause_to_id = cause_index(events)
    ctx = make_context(plan, cause_to_id)

    print(f"[spark-generate] cohort total individuals: {plan.total():,}")
    print(f"[spark-generate] migrations target:       {int(flows_per_decade.sum()):,}")
    print(f"[spark-generate] global seed: {GLOBAL_SEED}")

    ctx_payload = {
        "cohort_counts": plan.counts,
        "distance_km": ctx.distance_km,
        "region_centers": ctx.region_centers,
        "region_radii": ctx.region_radii,
        "region_continents": ctx.region_continents,
        "cause_to_id": ctx.cause_to_id,
    }
    events_payload = _events_payload(events)

    t0 = time.time()
    spark = _make_spark(scale)

    cohort_rows = []
    n_regions = geography.N_REGIONS
    for d in range(N_DECADES):
        for r in range(n_regions):
            c = int(plan.counts[d, r])
            if c > 0:
                cohort_rows.append((d, r, c))
    cohort_df = spark.createDataFrame(cohort_rows, ["decade_idx", "region_idx", "cohort_count"])

    individuals = cohort_df.groupby("decade_idx", "region_idx").applyInPandas(
        _cohort_apply_factory(ctx_payload),
        schema=_individual_schema(),
    )
    print(f"[spark-generate] writing {INDIVIDUALS_PATH} …")
    individuals.write.mode("overwrite").partitionBy("decade_idx").parquet(str(INDIVIDUALS_PATH))

    migration_rows = []
    for d in range(N_DECADES):
        slice_ = flows_per_decade[d]
        idxs = np.argwhere(slice_ > 0)
        for src, dst in idxs:
            migration_rows.append((d, int(src), int(dst), int(slice_[src, dst])))
    migration_df = spark.createDataFrame(
        migration_rows,
        ["decade_idx", "from_region_idx", "to_region_idx", "mig_count"],
    )
    migrations = migration_df.groupby("decade_idx", "from_region_idx", "to_region_idx").applyInPandas(
        _migration_apply_factory(ctx_payload, events_payload),
        schema=_migration_schema(),
    )
    print(f"[spark-generate] writing {MIGRATIONS_PATH} …")
    migrations.write.mode("overwrite").partitionBy("decade_idx").parquet(str(MIGRATIONS_PATH))

    elapsed = time.time() - t0
    print(f"[spark-generate] done in {elapsed:.1f}s")
    spark.stop()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scale", default="small", choices=list(SCALES.keys()),
                   help="Scale preset (default: small).")
    p.add_argument("--seed", type=int, default=None, help="Override the global seed.")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    run(scale_name=args.scale, seed=args.seed)
