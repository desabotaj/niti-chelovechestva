"""Loader for the historical events catalogue (events.yaml).

The simulator consumes events as plain dataclasses. Loading is centralised
here so PySpark workers can broadcast a single immutable list.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Pull:
    src: str
    dst: str
    weight: float
    reason: str


@dataclass(frozen=True)
class Event:
    id: str
    name: str
    start: int
    end: int
    type: str
    mortality: float = 1.0
    birth: float = 1.0
    regions: tuple[str, ...] = ()
    pulls: tuple[Pull, ...] = field(default_factory=tuple)
    description: str = ""

    def overlaps(self, year: int) -> bool:
        return self.start <= year < self.end + 1


EVENTS_YAML = Path(__file__).with_name("events.yaml")


def load_events(path: Path | None = None) -> list[Event]:
    src = path or EVENTS_YAML
    raw = yaml.safe_load(src.read_text(encoding="utf-8"))
    out: list[Event] = []
    for e in raw["events"]:
        pulls = tuple(
            Pull(p["from"], p["to"], float(p["weight"]), p.get("reason", ""))
            for p in e.get("pulls", []) or []
        )
        out.append(
            Event(
                id=e["id"],
                name=e["name"],
                start=int(e["start"]),
                end=int(e["end"]),
                type=e["type"],
                mortality=float(e.get("mortality", 1.0)),
                birth=float(e.get("birth", 1.0)),
                regions=tuple(e.get("regions", []) or []),
                pulls=pulls,
                description=e.get("description", ""),
            )
        )
    out.sort(key=lambda x: (x.start, x.id))
    return out


def events_active_in(year: int, events: list[Event]) -> list[Event]:
    return [e for e in events if e.overlaps(year)]


def event_window_summary(events: list[Event]) -> dict[int, list[str]]:
    """Map each year → list of event names active that year (for the UI ticker)."""
    out: dict[int, list[str]] = {}
    for ev in events:
        for y in range(ev.start, ev.end + 1):
            out.setdefault(y, []).append(ev.name)
    return out
