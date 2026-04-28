"""Migration model: gravity + event-driven pulls.

Outputs a 3-D probability cube `flow[decade, src, dst]` summing to 1
across (decade, src, dst). Combine with a global migration count
(per-scale config) to draw the actual events.

The model blends two terms:

  * **Gravity** baseline:  m_ij ∝ p_i * p_j / d_ij²
    — decays with great-circle distance, peaks between large populations.
  * **Event pulls**: explicit (src → dst, weight) entries from `events.yaml`
    overlapping the decade boost specific corridors. Slave trade,
    Volga Germans, Windrush, the 2015 European migrant crisis, etc.

A small "stay" probability keeps most flows local; the global mass we draw
from this cube is roughly proportional to a baseline migration rate plus
event spikes.
"""

from __future__ import annotations

import numpy as np

from . import geography
from .config import DECADES, N_DECADES
from .events import Event, events_active_in

BASE_MIGRATION_INTENSITY = 0.005
EVENT_MIGRATION_BOOST = 0.10
GRAVITY_DISTANCE_KM = 1500.0


def _gravity_weights(pop: np.ndarray, distance_km: np.ndarray) -> np.ndarray:
    """Return (N×N) gravity weights for the population vector `pop` (shape N)."""
    n = pop.shape[0]
    p_ij = np.outer(pop, pop)
    d = distance_km + GRAVITY_DISTANCE_KM
    w = p_ij / (d * d)
    np.fill_diagonal(w, 0.0)
    s = w.sum()
    return w / s if s > 0 else w


def _pulls_matrix(events: list[Event], region_idx: dict[str, int], year: int, n: int) -> np.ndarray:
    """Sparse pull-weight matrix for events active in `year`."""
    m = np.zeros((n, n), dtype=np.float64)
    for ev in events_active_in(year, events):
        for p in ev.pulls:
            i = region_idx.get(p.src)
            j = region_idx.get(p.dst)
            if i is None or j is None or i == j:
                continue
            m[i, j] += float(p.weight)
    return m


def flow_cube(events: list[Event], pop: np.ndarray) -> np.ndarray:
    """Return a (N_DECADES, N_REGIONS, N_REGIONS) flow probability cube.

    Each (decade, *, *) slice is normalised to 1 across all (src, dst)
    pairs, weighted by intensity (events boost a decade's mass).
    """
    n = geography.N_REGIONS
    region_idx = geography.region_index()
    distance = geography.pairwise_distance_km()

    cube = np.zeros((N_DECADES, n, n), dtype=np.float64)
    intensity = np.zeros(N_DECADES, dtype=np.float64)

    for d in range(N_DECADES):
        year = DECADES[d]
        gravity = _gravity_weights(np.maximum(pop[d], 1e-9), distance)
        pulls = _pulls_matrix(events, region_idx, year, n)
        active = events_active_in(year, events)
        boost = BASE_MIGRATION_INTENSITY + EVENT_MIGRATION_BOOST * len(active)
        intensity[d] = boost

        if pulls.sum() > 0:
            row_sums = pulls.sum(axis=1, keepdims=True)
            row_sums[row_sums == 0] = 1.0
            pulls_norm = pulls / row_sums
            blend = 0.7 * pulls_norm + 0.3 * (gravity / np.maximum(gravity.sum(axis=1, keepdims=True), 1e-12))
        else:
            blend = gravity / np.maximum(gravity.sum(axis=1, keepdims=True), 1e-12)

        out_share = pop[d] / max(pop[d].sum(), 1e-12)
        slice_ = (out_share[:, None] * blend) * boost
        cube[d] = slice_

    total = cube.sum()
    return cube / total if total > 0 else cube


def cause_index(events: list[Event]) -> dict[str, int]:
    """Map event id → small int for compact `cause` column."""
    out = {"baseline": 0}
    for i, ev in enumerate(events, start=1):
        out[ev.id] = i
    return out


def primary_event_for(year: int, src_idx: int, dst_idx: int, events: list[Event],
                      region_idx: dict[str, int]) -> str:
    """Pick the most weighted event explaining a (year, src, dst) flow.

    Used to label migration events with a meaningful cause for the UI.
    """
    best_id = "baseline"
    best_w = 0.0
    for ev in events_active_in(year, events):
        for p in ev.pulls:
            if region_idx.get(p.src) == src_idx and region_idx.get(p.dst) == dst_idx:
                if p.weight > best_w:
                    best_w = p.weight
                    best_id = ev.id
    return best_id


def yearly_decomposition(decade_idx: int, mass: int, rng: np.random.Generator) -> np.ndarray:
    """Spread a decade's migrations roughly uniformly across the 10 years.

    Returns a length-10 int vector summing to `mass`.
    """
    if mass <= 0:
        return np.zeros(10, dtype=np.int64)
    fractions = rng.dirichlet(np.full(10, 4.0))
    base = (fractions * mass).astype(np.int64)
    short = mass - int(base.sum())
    if short > 0:
        order = np.argsort(-fractions)
        base[order[:short]] += 1
    return base
