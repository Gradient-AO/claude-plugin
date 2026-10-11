#!/usr/bin/env python3
"""Validate a manager-performance report through the mode registry."""

from __future__ import annotations

import sys
from pathlib import Path


PLUGIN_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PLUGIN_ROOT / "tools"))

from idd_report_validator import run_idd_cli  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(run_idd_cli(sys.argv))
