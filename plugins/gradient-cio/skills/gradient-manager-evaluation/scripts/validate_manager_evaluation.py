#!/usr/bin/env python3
"""Validate single, fit, or compare manager-evaluation reports."""

from __future__ import annotations

import json
import sys
from pathlib import Path


PLUGIN_SHARED = Path(__file__).resolve().parents[3] / "shared"
if str(PLUGIN_SHARED) not in sys.path:
    sys.path.insert(0, str(PLUGIN_SHARED))

from idd_report_validator import run_idd_cli, run_named_idd_cli  # noqa: E402


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <report.json>")
        return 2
    try:
        document = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR — {error}")
        return 2
    mode = document.get("meta", {}).get("mode")
    if mode == "fit":
        return run_named_idd_cli(argv, "portfolio_fit")
    if mode in {"single", "compare"}:
        return run_idd_cli(argv, expected_mode=mode)
    print("FAIL — manager evaluation: meta.mode must be single, fit, or compare")
    return 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
