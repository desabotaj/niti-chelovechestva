"""Deterministic ID packing & synthetic parent assignment.

Every individual lives in a (decade, region) "cohort" with a within-cohort
index. We pack that triple into a 64-bit ID so parent ↔ child relationships
can be sampled without ever joining tables — important for keeping the
PySpark pipeline embarrassingly parallel even at billion-row scale.

Layout (top-to-bottom MSB):

    [6 bits  decade  ][6 bits  region][52 bits  within-cohort idx]

That's 2^52 ≈ 4.5×10^15 people per cohort, more than we ever need.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import geography
from .config import GLOBAL_SEED, N_DECADES

DECADE_BITS = 6
REGION_BITS = 6
INDEX_BITS = 64 - DECADE_BITS - REGION_BITS
INDEX_MASK = (1 << INDEX_BITS) - 1
REGION_MASK = (1 << REGION_BITS) - 1
DECADE_SHIFT = REGION_BITS + INDEX_BITS
REGION_SHIFT = INDEX_BITS

NULL_ID = np.int64(-1)


def pack_id(decade_idx: np.ndarray, region_idx: np.ndarray, within_idx: np.ndarray) -> np.ndarray:
    """Pack (decade, region, within) → int64 id."""
    d = np.asarray(decade_idx, dtype=np.int64) & ((1 << DECADE_BITS) - 1)
    r = np.asarray(region_idx, dtype=np.int64) & REGION_MASK
    i = np.asarray(within_idx, dtype=np.int64) & INDEX_MASK
    return (d << DECADE_SHIFT) | (r << REGION_SHIFT) | i


def unpack_id(packed: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p = np.asarray(packed, dtype=np.int64)
    d = (p >> DECADE_SHIFT) & ((1 << DECADE_BITS) - 1)
    r = (p >> REGION_SHIFT) & REGION_MASK
    i = p & INDEX_MASK
    return d, r, i


@dataclass(frozen=True)
class CohortPlan:
    """How many individuals to spawn per (decade, region)."""

    counts: np.ndarray

    def total(self) -> int:
        return int(self.counts.sum())

    def cohort_size(self, decade_idx: int, region_idx: int) -> int:
        return int(self.counts[decade_idx, region_idx])

    def safe_size(self, decade_idx: int, region_idx: int) -> int:
        return max(self.cohort_size(decade_idx, region_idx), 1)


def cohort_plan_from_weights(weights: np.ndarray, total_individuals: int) -> CohortPlan:
    """Allocate `total_individuals` across cohorts proportional to `weights`.

    Uses largest-remainder rounding so the totals match exactly.
    """
    flat = weights.ravel()
    s = flat.sum()
    if s <= 0:
        raise ValueError("Birth weights sum to zero")
    fractional = flat / s * total_individuals
    base = np.floor(fractional).astype(np.int64)
    remainder = total_individuals - int(base.sum())
    if remainder > 0:
        order = np.argsort(-(fractional - base))
        base[order[:remainder]] += 1
    return CohortPlan(counts=base.reshape(weights.shape))


PARENT_DECADE_OFFSETS = np.array([2, 3], dtype=np.int64)


def sample_parent_within(rng: np.random.Generator, cohort_size: int, n: int) -> np.ndarray:
    if cohort_size <= 0:
        return np.full(n, -1, dtype=np.int64)
    return rng.integers(0, cohort_size, size=n, dtype=np.int64)


def parent_region_kernel(child_region: int, distance_km: np.ndarray, sigma_km: float = 800.0) -> np.ndarray:
    """Probability that a parent of a child in `child_region` was born in each region.

    Gaussian decay over great-circle distance — most parents are local,
    rare long-range "founder ancestors" represent old migration tails.
    """
    d = distance_km[child_region]
    w = np.exp(-(d ** 2) / (2.0 * sigma_km ** 2))
    s = w.sum()
    return w / s if s > 0 else w


def assemble_parent_ids(
    rng: np.random.Generator,
    child_decade_idx: int,
    child_region_idx: int,
    n: int,
    cohort_plan: CohortPlan,
    distance_km: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Return (parent1_ids, parent2_ids) of length n for the given child cohort.

    Parents are drawn from the child's own region with high probability and
    from nearby regions otherwise. Any pick whose target cohort is empty is
    deterministically remapped to the child's region — guaranteeing that
    every parent_id references a real generated row.
    """
    n_regions = geography.N_REGIONS
    if child_decade_idx < int(PARENT_DECADE_OFFSETS.min()):
        return (np.full(n, NULL_ID, dtype=np.int64), np.full(n, NULL_ID, dtype=np.int64))

    region_probs = parent_region_kernel(child_region_idx, distance_km)
    sampled_regions_1 = rng.choice(n_regions, size=n, p=region_probs)
    sampled_regions_2 = rng.choice(n_regions, size=n, p=region_probs)

    offsets_1 = rng.choice(PARENT_DECADE_OFFSETS, size=n)
    offsets_2 = rng.choice(PARENT_DECADE_OFFSETS, size=n)
    parent_decades_1 = np.maximum(child_decade_idx - offsets_1, 0)
    parent_decades_2 = np.maximum(child_decade_idx - offsets_2, 0)

    counts = cohort_plan.counts

    def _resolve(parent_decades: np.ndarray, parent_regions: np.ndarray):
        parent_decades = parent_decades.copy()
        parent_regions = parent_regions.copy()
        sizes = counts[parent_decades, parent_regions]
        empty_idx = np.where(sizes == 0)[0]
        for i in empty_idx:
            d = int(parent_decades[i])
            if counts[d, child_region_idx] > 0:
                parent_regions[i] = child_region_idx
                continue
            row = counts[d]
            row_sum = int(row.sum())
            if row_sum > 0:
                p = row / row_sum
                parent_regions[i] = int(rng.choice(n_regions, p=p))
            else:
                d_alt = max(d - 1, 0)
                row_alt = counts[d_alt]
                if row_alt.sum() > 0:
                    p = row_alt / row_alt.sum()
                    parent_decades[i] = d_alt
                    parent_regions[i] = int(rng.choice(n_regions, p=p))
        sizes = counts[parent_decades, parent_regions]
        sizes = np.maximum(sizes, 1)
        return parent_decades, parent_regions, sizes

    parent_decades_1, sampled_regions_1, cohort_sizes_1 = _resolve(parent_decades_1, sampled_regions_1)
    parent_decades_2, sampled_regions_2, cohort_sizes_2 = _resolve(parent_decades_2, sampled_regions_2)

    within_1 = (rng.integers(0, np.iinfo(np.int64).max, size=n, dtype=np.int64)) % cohort_sizes_1
    within_2 = (rng.integers(0, np.iinfo(np.int64).max, size=n, dtype=np.int64)) % cohort_sizes_2

    p1 = pack_id(parent_decades_1, sampled_regions_1, within_1)
    p2 = pack_id(parent_decades_2, sampled_regions_2, within_2)
    return p1, p2


def child_seed(decade_idx: int, region_idx: int, salt: int = 0) -> int:
    return (GLOBAL_SEED ^ (decade_idx * 1_000_003) ^ (region_idx * 31337) ^ salt) & 0xFFFFFFFF


def n_decades() -> int:
    return N_DECADES
