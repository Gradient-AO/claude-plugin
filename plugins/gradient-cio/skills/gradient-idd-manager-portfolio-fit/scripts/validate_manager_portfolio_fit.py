#!/usr/bin/env python3
"""Validate a manager portfolio-fit report through its strict contract."""

from __future__ import annotations

import sys
from pathlib import Path


SCRIPT_ROOT = Path(__file__).resolve().parent
if str(SCRIPT_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_ROOT))

from idd_report_validator import run_named_idd_cli  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(run_named_idd_cli(sys.argv, "portfolio_fit"))
