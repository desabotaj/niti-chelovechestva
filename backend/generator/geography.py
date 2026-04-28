"""Region definitions: 46 anchor zones spanning the inhabited world.

Each region carries a center coordinate, an initial-population share for
year 1525, an ethnocultural macro-vector, and a continent label. These
seeds are the only "geographic ground truth" the simulator needs: H3
cells are derived per individual by jittering around the region centre.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ETHNO_GROUPS = (
    "european",
    "mena",
    "subsaharan",
    "south_asian",
    "east_asian",
    "southeast_asian",
    "amerindian",
    "pacific",
)


@dataclass(frozen=True)
class Region:
    id: str
    name: str
    lat: float
    lon: float
    pop_share: float
    continent: str
    ethno: tuple[float, ...]
    radius_deg: float = 4.0


def _vec(**kwargs: float) -> tuple[float, ...]:
    base = dict.fromkeys(ETHNO_GROUPS, 0.0)
    base.update(kwargs)
    s = sum(base.values()) or 1.0
    return tuple(base[k] / s for k in ETHNO_GROUPS)


REGIONS: tuple[Region, ...] = (
    # ── Europe ──────────────────────────────────────────────────────────
    Region("gbr", "British Isles",     54.5,  -2.5,   4.0, "Europe", _vec(european=1.0), 3.0),
    Region("fra", "France",            46.5,   2.5,  16.0, "Europe", _vec(european=1.0), 3.0),
    Region("deu", "Germany",           51.0,  10.5,  16.0, "Europe", _vec(european=1.0), 3.0),
    Region("nld", "Low Countries",     52.0,   5.0,   1.5, "Europe", _vec(european=1.0), 1.5),
    Region("esp", "Iberia (Spain)",    40.0,  -3.5,   7.0, "Europe", _vec(european=0.95, mena=0.05), 3.5),
    Region("prt", "Iberia (Portugal)", 39.5,  -8.0,   1.5, "Europe", _vec(european=0.95, mena=0.05), 1.5),
    Region("ita", "Italy",             42.5,  12.5,  11.0, "Europe", _vec(european=0.95, mena=0.05), 3.5),
    Region("sca", "Scandinavia",       60.0,  15.0,   1.5, "Europe", _vec(european=1.0), 6.0),
    Region("pol", "Poland",            52.0,  20.0,   4.0, "Europe", _vec(european=1.0), 3.5),
    Region("rus_eu","European Russia", 56.0,  37.5,   9.0, "Europe", _vec(european=1.0), 8.0),
    Region("ukr", "Ukraine",           49.5,  31.5,   3.5, "Europe", _vec(european=1.0), 4.0),
    Region("bal", "Balkans",           43.5,  21.0,   6.0, "Europe", _vec(european=0.85, mena=0.15), 4.0),

    # ── Middle East / Caucasus / Central Asia ───────────────────────────
    Region("tur", "Anatolia",          39.0,  35.5,   8.0, "MENA",   _vec(mena=0.95, european=0.05), 4.0),
    Region("lev", "Levant",            34.0,  36.5,   4.0, "MENA",   _vec(mena=1.0), 2.5),
    Region("arab","Arabian Peninsula", 24.0,  45.0,   4.0, "MENA",   _vec(mena=1.0), 6.0),
    Region("per", "Iranian Plateau",   33.0,  53.5,   6.0, "MENA",   _vec(mena=0.85, south_asian=0.15), 5.5),
    Region("cas", "Central Asia",      42.0,  68.0,   4.0, "Asia",   _vec(east_asian=0.4, mena=0.4, south_asian=0.2), 7.0),
    Region("mar", "Maghreb",           32.0,   3.0,   6.0, "MENA",   _vec(mena=1.0), 6.0),
    Region("egy", "Egypt",             27.5,  30.5,   4.0, "MENA",   _vec(mena=1.0), 3.0),

    # ── Sub-Saharan Africa ──────────────────────────────────────────────
    Region("waf", "West Africa",       11.0,   2.0,  25.0, "Africa", _vec(subsaharan=1.0), 7.0),
    Region("caf", "Central Africa",    -1.0,  20.0,   8.0, "Africa", _vec(subsaharan=1.0), 6.0),
    Region("eaf", "East Africa",       -2.0,  37.0,  12.0, "Africa", _vec(subsaharan=1.0), 5.0),
    Region("hoa", "Horn of Africa",    9.0,   42.5,   4.0, "Africa", _vec(subsaharan=0.7, mena=0.3), 4.0),
    Region("saf", "Southern Africa",  -25.0,  27.0,   5.0, "Africa", _vec(subsaharan=1.0), 6.0),

    # ── South Asia ──────────────────────────────────────────────────────
    Region("ind_n","North India",     27.0,  78.0,  50.0, "Asia",   _vec(south_asian=1.0), 4.0),
    Region("ind_s","South India",     13.0,  78.0,  35.0, "Asia",   _vec(south_asian=1.0), 4.0),
    Region("ben", "Bengal",            23.5,  90.0,  25.0, "Asia",   _vec(south_asian=1.0), 2.5),
    Region("pak", "Indus / Pakistan", 30.0,  70.0,   8.0, "Asia",   _vec(south_asian=0.85, mena=0.15), 4.0),

    # ── East Asia ───────────────────────────────────────────────────────
    Region("chn_n","North China",     38.0, 115.0,  65.0, "Asia",   _vec(east_asian=1.0), 5.0),
    Region("chn_s","South China",     26.0, 113.0,  60.0, "Asia",   _vec(east_asian=1.0), 5.0),
    Region("jpn", "Japan",             36.0, 138.0,  16.0, "Asia",   _vec(east_asian=1.0), 4.0),
    Region("kor", "Korea",             37.5, 127.5,   6.0, "Asia",   _vec(east_asian=1.0), 1.5),
    Region("twn", "Taiwan",            23.5, 121.0,   0.4, "Asia",   _vec(east_asian=1.0), 1.0),

    # ── Southeast Asia ──────────────────────────────────────────────────
    Region("idn", "Indonesia",         -3.0, 117.0,   8.0, "Asia",   _vec(southeast_asian=1.0), 8.0),
    Region("phl", "Philippines",       12.0, 122.0,   0.6, "Asia",   _vec(southeast_asian=0.95, pacific=0.05), 4.0),
    Region("vnm", "Vietnam",           16.0, 107.0,   5.0, "Asia",   _vec(southeast_asian=1.0), 3.5),
    Region("tha", "Mainland SE Asia",  16.0, 102.0,   4.0, "Asia",   _vec(southeast_asian=1.0), 4.0),
    Region("mly", "Malay Peninsula",    4.0, 102.0,   1.0, "Asia",   _vec(southeast_asian=0.95, east_asian=0.05), 2.5),

    # ── North America ───────────────────────────────────────────────────
    Region("usa_ne","US Northeast",   42.0, -73.0,   0.6, "Americas", _vec(amerindian=1.0), 3.0),
    Region("usa_ma","US Mid-Atlantic",39.5, -77.0,   0.5, "Americas", _vec(amerindian=1.0), 3.0),
    Region("usa_se","US Southeast",   33.0, -83.0,   1.0, "Americas", _vec(amerindian=1.0), 4.0),
    Region("usa_mw","US Midwest",     41.5, -90.0,   1.5, "Americas", _vec(amerindian=1.0), 5.0),
    Region("usa_w", "US West",        37.0,-118.0,   1.5, "Americas", _vec(amerindian=1.0), 6.0),
    Region("can",  "Canada",           53.0, -100.0,   0.4, "Americas", _vec(amerindian=1.0), 9.0),
    Region("mex",  "Mexico",           23.5, -102.0,  18.0, "Americas", _vec(amerindian=1.0), 5.0),
    Region("cam",  "Central America",  14.0,  -88.5,   5.0, "Americas", _vec(amerindian=1.0), 3.0),
    Region("car",  "Caribbean",        18.0,  -75.0,   5.0, "Americas", _vec(amerindian=1.0), 5.0),

    # ── South America ───────────────────────────────────────────────────
    Region("bra_ne","Brazil — Northeast", -8.0, -38.0,   4.0, "Americas", _vec(amerindian=1.0), 4.0),
    Region("bra_se","Brazil — Southeast",-22.0, -45.0,   1.0, "Americas", _vec(amerindian=1.0), 5.0),
    Region("arg",  "Río de la Plata", -34.0, -60.5,   0.6, "Americas", _vec(amerindian=1.0), 6.0),
    Region("and",  "Andean",           -7.0,  -75.0,  18.0, "Americas", _vec(amerindian=1.0), 7.0),

    # ── Oceania ─────────────────────────────────────────────────────────
    Region("aus", "Australia",        -25.5, 134.0,   0.5, "Oceania", _vec(pacific=1.0), 9.0),
    Region("nzl", "New Zealand",      -41.0, 173.0,   0.05,"Oceania", _vec(pacific=1.0), 3.0),
    Region("oce", "Pacific Islands",   -7.0, 160.0,   0.3, "Oceania", _vec(pacific=1.0), 12.0),
)

REGIONS_BY_ID: dict[str, Region] = {r.id: r for r in REGIONS}
N_REGIONS = len(REGIONS)


def normalised_initial_pop_shares() -> dict[str, float]:
    total = sum(r.pop_share for r in REGIONS) or 1.0
    return {r.id: r.pop_share / total for r in REGIONS}


def initial_pop_array() -> np.ndarray:
    """Returns the initial 1525 population shares aligned with REGIONS order."""
    shares = normalised_initial_pop_shares()
    return np.array([shares[r.id] for r in REGIONS], dtype=np.float64)


def region_centers() -> np.ndarray:
    """Nx2 array of (lat, lon) centres aligned with REGIONS order."""
    return np.array([(r.lat, r.lon) for r in REGIONS], dtype=np.float64)


def region_radii_deg() -> np.ndarray:
    """N-vector of jitter radii (degrees) aligned with REGIONS order."""
    return np.array([r.radius_deg for r in REGIONS], dtype=np.float64)


def region_ethno_matrix() -> np.ndarray:
    """N×8 matrix of ethnocultural macro vectors aligned with REGIONS order."""
    return np.array([r.ethno for r in REGIONS], dtype=np.float64)


def region_index() -> dict[str, int]:
    return {r.id: i for i, r in enumerate(REGIONS)}


def haversine_km(lat1: np.ndarray, lon1: np.ndarray, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Vectorised haversine distance (km) between matched coordinate arrays."""
    R = 6371.0088
    lat1r, lat2r = np.radians(lat1), np.radians(lat2)
    dlat = lat2r - lat1r
    dlon = np.radians(lon2 - lon1)
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    return 2.0 * R * np.arcsin(np.sqrt(a))


def pairwise_distance_km() -> np.ndarray:
    """N×N matrix of great-circle distances between region centres (km)."""
    centers = region_centers()
    lat = centers[:, 0]
    lon = centers[:, 1]
    lat1, lat2 = np.meshgrid(lat, lat, indexing="ij")
    lon1, lon2 = np.meshgrid(lon, lon, indexing="ij")
    return haversine_km(lat1, lon1, lat2, lon2)


def jitter_in_region(rng: np.random.Generator, region_idx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Sample (lat, lon) coordinates for `region_idx[i]` jittered around the centre.

    Uses a Gaussian-on-the-sphere approximation: longitude jitter is scaled by
    1/cos(lat) so cells of equal area come out at all latitudes.
    """
    centers = region_centers()
    radii = region_radii_deg()
    lat0 = centers[region_idx, 0]
    lon0 = centers[region_idx, 1]
    r = radii[region_idx]
    lat_noise = rng.normal(0.0, r * 0.5)
    cos_lat = np.cos(np.radians(lat0))
    lon_noise = rng.normal(0.0, r * 0.5) / np.maximum(cos_lat, 0.2)
    lat = np.clip(lat0 + lat_noise, -85.0, 85.0)
    lon = ((lon0 + lon_noise + 180.0) % 360.0) - 180.0
    return lat.astype(np.float32), lon.astype(np.float32)
