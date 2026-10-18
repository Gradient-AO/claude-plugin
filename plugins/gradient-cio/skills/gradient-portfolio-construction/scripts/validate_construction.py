#!/usr/bin/env python3
"""Validate a portfolio-construction report through the mode registry."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from construction_report_validator import run_construction_cli  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(run_construction_cli(sys.argv))
