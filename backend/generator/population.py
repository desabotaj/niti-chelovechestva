"""Population dynamics: deterministic per-region per-decade trajectories.

We model each region with a Malthusian-logistic equation modulated by
historical events. The output is a `(N_DECADES, N_REGIONS)` matrix giving
the population *index* at the end of each decade (relative to its own
1525 baseline) plus a `(N_DECADES, N_REGIONS)` matrix of "spawn weights"
— how many newborns each region should contribute that decade.

These are NOT real demographic numbers; they are calibrated so that the
sum over the full 1525-2025 window matches a coarse global trajectory
(world pop ~500M → ~8B) and so that historical shocks leave visible
dents.
"""

from __future__ import annotations

import numpy as np

from . import geography
from .config import DECADES, GLOBAL_SEED, N_DECADES
from .events import Event, events_active_in

CRUDE_BIRTH_BY_DECADE = np.linspace(0.040, 0.012, N_DECADES)
CRUDE_DEATH_BY_DECADE = np.linspace(0.035, 0.008, N_DECADES)

CARRYING_CAPACITY_GROWTH = np.linspace(1.0, 25.0, N_DECADES)


def _apply_event_factors(
    year: int,
    events: list[Event],
    region_index: dict[str, int],
    n_regions: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Per-region (mortality_factor, birth_factor) for the given year."""
    mort = np.ones(n_regions, dtype=np.float64)
    birth = np.ones(n_regions, dtype=np.float64)
    for ev in events_active_in(year, events):
        if not ev.regions:
            continue
        for rid in ev.regions:
            if rid in region_index:
                idx = region_index[rid]
                mort[idx] = max(mort[idx], ev.mortality)
                birth[idx] = min(birth[idx], ev.birth)
    return mort, birth


def population_trajectory(events: list[Event], total_world_1525: float = 1.0) -> np.ndarray:
    """Compute a (N_DECADES, N_REGIONS) population matrix.

    Values are in the same units as `total_world_1525`. Use 1.0 for a
    normalised trajectory; the actual cohort sizes are scaled later.
    """
    n_regions = geography.N_REGIONS
    region_idx = geography.region_index()
    pop = np.zeros((N_DECADES, n_regions), dtype=np.float64)
    pop[0] = geography.initial_pop_array() * total_world_1525

    for d in range(1, N_DECADES):
        decade_year = DECADES[d]
        mort_f, birth_f = _apply_event_factors(decade_year, events, region_idx, n_regions)
        decade_births = CRUDE_BIRTH_BY_DECADE[d] * 10.0 * birth_f
        decade_deaths = CRUDE_DEATH_BY_DECADE[d] * 10.0 * mort_f
        net = decade_births - decade_deaths

        carrying = pop[0] * CARRYING_CAPACITY_GROWTH[d]
        carrying = np.maximum(carrying, 1e-9)
        log_factor = 1.0 - pop[d - 1] / carrying
        log_factor = np.clip(log_factor, -0.5, 1.0)

        pop[d] = pop[d - 1] * (1.0 + net * log_factor)
        pop[d] = np.maximum(pop[d], pop[d - 1] * 0.5)

    return pop


def normalised_birth_weights(pop: np.ndarray, events: list[Event]) -> np.ndarray:
    """Per-(decade, region) probability weight that a newborn is sampled there.

    Combines mid-decade population × event-modulated birth rate.
    """
    n_regions = geography.N_REGIONS
    region_idx = geography.region_index()
    w = np.zeros_like(pop)
    for d in range(N_DECADES):
        decade_year = DECADES[d]
        _, birth_f = _apply_event_factors(decade_year, events, region_idx, n_regions)
        midpop = pop[d] if d == 0 else 0.5 * (pop[d - 1] + pop[d])
        w[d] = midpop * birth_f * CRUDE_BIRTH_BY_DECADE[d]
    total = w.sum()
    return w / total if total > 0 else w


def lifespan_distribution(decade_idx: int, rng: np.random.Generator, n: int) -> np.ndarray:
    """Sample n lifespans appropriate for the given decade index.

    Pre-modern: bimodal (high infant mortality + adult ~50 years).
    Modern: shifted Gaussian centred on ~75.
    """
    progress = decade_idx / max(N_DECADES - 1, 1)
    infant_share = 0.30 * (1.0 - progress) + 0.02
    adult_mean = 45.0 + 35.0 * progress
    adult_sd = 12.0 - 4.0 * progress

    mask_infant = rng.random(n) < infant_share
    out = np.empty(n, dtype=np.int16)
    n_infant = int(mask_infant.sum())
    out[mask_infant] = rng.integers(0, 8, size=n_infant, dtype=np.int16)
    n_adult = n - n_infant
    adult_lifespans = rng.normal(adult_mean, adult_sd, size=n_adult)
    out[~mask_infant] = np.clip(adult_lifespans, 10, 100).astype(np.int16)
    return out


def make_rng(decade_idx: int, region_idx: int, salt: int = 0) -> np.random.Generator:
    """Stable per-(decade, region) RNG so results are reproducible & shardable."""
    seed = (GLOBAL_SEED * 1_000_003) ^ (decade_idx * 7919) ^ (region_idx * 31337) ^ salt
    return np.random.default_rng(seed & 0xFFFFFFFF)
