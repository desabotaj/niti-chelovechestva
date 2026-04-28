"""Vectorised cohort & migration row generators.

Both the PySpark pipeline (`spark_generate.py`) and the local Polars
pipeline (`local_generate.py`) call into here, so the actual row-level
synthesis logic lives in one place. The functions return Pandas
DataFrames matching the Parquet schemas exactly.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import geography
from .config import DECADES
from .events import Event
from .genealogy import CohortPlan, assemble_parent_ids, pack_id
from .migration import primary_event_for
from .population import lifespan_distribution, make_rng


@dataclass(frozen=True)
class SpawnContext:
    cohort_plan: CohortPlan
    distance_km: np.ndarray
    region_centers: np.ndarray
    region_radii: np.ndarray
    region_continents: tuple[str, ...]
    cause_to_id: dict[str, int]


def make_context(cohort_plan: CohortPlan, cause_to_id: dict[str, int]) -> SpawnContext:
    return SpawnContext(
        cohort_plan=cohort_plan,
        distance_km=geography.pairwise_distance_km(),
        region_centers=geography.region_centers(),
        region_radii=geography.region_radii_deg(),
        region_continents=tuple(r.continent for r in geography.REGIONS),
        cause_to_id=cause_to_id,
    )


def _jitter(rng: np.random.Generator, region_idx: int, n: int,
            centers: np.ndarray, radii: np.ndarray, scale: float = 0.5) -> tuple[np.ndarray, np.ndarray]:
    lat0 = centers[region_idx, 0]
    lon0 = centers[region_idx, 1]
    r = radii[region_idx]
    cos_lat = np.cos(np.radians(lat0))
    lat = np.clip(lat0 + rng.normal(0.0, r * scale, size=n), -85.0, 85.0).astype(np.float32)
    lon_noise = rng.normal(0.0, r * scale, size=n) / max(cos_lat, 0.2)
    lon = (((lon0 + lon_noise) + 180.0) % 360.0 - 180.0).astype(np.float32)
    return lat, lon


def spawn_cohort(decade_idx: int, region_idx: int, n: int, ctx: SpawnContext) -> pd.DataFrame:
    if n <= 0:
        return pd.DataFrame()

    rng = make_rng(decade_idx, region_idx, salt=11)
    within = np.arange(n, dtype=np.int64)
    ids = pack_id(np.full(n, decade_idx), np.full(n, region_idx), within)

    decade_year = DECADES[decade_idx]
    birth_years = (decade_year + rng.integers(0, 10, size=n)).astype(np.int16)
    lifespans = lifespan_distribution(decade_idx, rng, n)
    death_years = np.clip(birth_years.astype(np.int32) + lifespans, decade_year, 2100).astype(np.int16)

    sex = rng.integers(0, 2, size=n, dtype=np.int8)

    birth_lat, birth_lon = _jitter(rng, region_idx, n, ctx.region_centers, ctx.region_radii, scale=0.5)

    p1, p2 = assemble_parent_ids(rng, decade_idx, region_idx, n, ctx.cohort_plan, ctx.distance_km)

    return pd.DataFrame(
        {
            "id": ids,
            "birth_year": birth_years,
            "death_year": death_years,
            "birth_region_idx": np.full(n, region_idx, dtype=np.int8),
            "birth_lat": birth_lat,
            "birth_lon": birth_lon,
            "sex": sex,
            "parent1_id": p1.astype(np.int64),
            "parent2_id": p2.astype(np.int64),
            "birth_continent": ctx.region_continents[region_idx],
            "decade_idx": np.full(n, decade_idx, dtype=np.int32),
        }
    )


def spawn_migration_batch(
    decade_idx: int,
    src: int,
    dst: int,
    n: int,
    events: list[Event],
    ctx: SpawnContext,
) -> pd.DataFrame:
    if n <= 0:
        return pd.DataFrame()

    rng = make_rng(decade_idx, src * 100 + dst, salt=29)
    decade_year = DECADES[decade_idx]
    years = (decade_year + rng.integers(0, 10, size=n)).astype(np.int16)

    parent_decades = np.maximum(decade_idx - rng.integers(1, 4, size=n), 0).astype(np.int64)
    cohort_sizes = np.array(
        [max(int(ctx.cohort_plan.cohort_size(int(d), src)), 1) for d in parent_decades],
        dtype=np.int64,
    )
    within = (rng.integers(0, np.iinfo(np.int64).max, size=n, dtype=np.int64)) % cohort_sizes
    person_ids = pack_id(parent_decades, np.full(n, src), within)

    from_lat, from_lon = _jitter(rng, src, n, ctx.region_centers, ctx.region_radii, scale=0.4)
    to_lat, to_lon = _jitter(rng, dst, n, ctx.region_centers, ctx.region_radii, scale=0.4)

    region_idx_map = geography.region_index()
    cause_label = primary_event_for(int(years[0]), src, dst, events, region_idx_map)
    cause_id = ctx.cause_to_id.get(cause_label, 0)

    return pd.DataFrame(
        {
            "person_id": person_ids,
            "year": years,
            "from_region_idx": np.full(n, src, dtype=np.int8),
            "to_region_idx": np.full(n, dst, dtype=np.int8),
            "from_lat": from_lat,
            "from_lon": from_lon,
            "to_lat": to_lat,
            "to_lon": to_lon,
            "cause_id": np.full(n, cause_id, dtype=np.int32),
            "cause_label": cause_label,
            "decade_idx": np.full(n, decade_idx, dtype=np.int32),
        }
    )
