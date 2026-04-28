"""Global configuration & scale presets for the Threads of Humanity pipeline.

A single deterministic seed reproduces the whole dataset. Scale presets let
the same code run on a laptop (tiny / small) or scale up to "true big-data"
runs (medium / big) on a beefier machine or cluster.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

START_YEAR = 1525
END_YEAR = 2025
YEARS = END_YEAR - START_YEAR
DECADES = list(range(START_YEAR, END_YEAR, 10))
N_DECADES = len(DECADES)

H3_RES_AGG = 3
H3_RES_FINE = 5

GLOBAL_SEED = 20260429


@dataclass(frozen=True)
class ScalePreset:
    name: str
    initial_population: int
    description: str
    spark_partitions: int


SCALES: dict[str, ScalePreset] = {
    "tiny": ScalePreset(
        name="tiny",
        initial_population=20_000,
        description="Smoke-test scale (~120 MB total). Runs end-to-end in seconds.",
        spark_partitions=4,
    ),
    "small": ScalePreset(
        name="small",
        initial_population=200_000,
        description="Default demo scale (~1-2 GB). Runs end-to-end in 1-3 minutes on a laptop.",
        spark_partitions=16,
    ),
    "medium": ScalePreset(
        name="medium",
        initial_population=2_000_000,
        description="Serious single-machine run (~15-25 GB). Needs ≥32 GB RAM.",
        spark_partitions=64,
    ),
    "big": ScalePreset(
        name="big",
        initial_population=20_000_000,
        description="True big-data scale (~150-300 GB). Designed for a cluster run.",
        spark_partitions=512,
    ),
}


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = REPO_ROOT / "backend"
DATA_ROOT = BACKEND_ROOT / "data"
FRONTEND_DATA = REPO_ROOT / "frontend" / "public" / "data"

INDIVIDUALS_PATH = DATA_ROOT / "individuals.parquet"
MIGRATIONS_PATH = DATA_ROOT / "migrations.parquet"
HEX_AGG_PATH = DATA_ROOT / "hex_agg.parquet"
ARCS_PATH = DATA_ROOT / "arcs.parquet"
LINEAGES_PATH = DATA_ROOT / "lineages.parquet"


def ensure_dirs() -> None:
    for p in (DATA_ROOT, FRONTEND_DATA):
        p.mkdir(parents=True, exist_ok=True)
