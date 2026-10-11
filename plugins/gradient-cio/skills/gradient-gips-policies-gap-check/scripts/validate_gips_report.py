#!/usr/bin/env python3
"""Run the canonical strict GIPS report validator."""

from __future__ import annotations

import runpy
from pathlib import Path


CANONICAL = (
    Path(__file__).resolve().parents[2]
    / "gradient-gips-standards"
    / "scripts"
    / "validate_gips_report.py"
)

if __name__ == "__main__":
    runpy.run_path(str(CANONICAL), run_name="__main__")
