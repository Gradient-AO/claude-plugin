#!/usr/bin/env python3
"""Validate a fixed-income construction report through the shared registry."""

from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from construction_report_validator import run_construction_cli  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(run_construction_cli(sys.argv, "fixed_income"))
