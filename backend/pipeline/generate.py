"""End-to-end pipeline: generate → aggregate → export.

    python -m pipeline.generate --scale small --engine local

`--engine` picks between `local` (Polars/PyArrow, no JVM needed) and
`spark` (PySpark; the same code paths used in cluster runs).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PKG_ROOT = Path(__file__).resolve().parents[1]
if str(PKG_ROOT) not in sys.path:
    sys.path.insert(0, str(PKG_ROOT))

from generator.config import SCALES

from pipeline import aggregate, export, local_generate


def run(scale: str, engine: str, skip_generate: bool = False, skip_aggregate: bool = False,
        skip_export: bool = False) -> None:
    if not skip_generate:
        if engine == "local":
            local_generate.run(scale_name=scale)
        elif engine == "spark":
            from pipeline import spark_generate
            spark_generate.run(scale_name=scale)
        else:
            raise ValueError(f"Unknown engine: {engine}")
    if not skip_aggregate:
        aggregate.run()
    if not skip_export:
        export.run()


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scale", default="small", choices=list(SCALES.keys()))
    p.add_argument("--engine", default="local", choices=["local", "spark"])
    p.add_argument("--skip-generate", action="store_true")
    p.add_argument("--skip-aggregate", action="store_true")
    p.add_argument("--skip-export", action="store_true")
    return p.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    run(
        scale=args.scale,
        engine=args.engine,
        skip_generate=args.skip_generate,
        skip_aggregate=args.skip_aggregate,
        skip_export=args.skip_export,
    )
