#!/usr/bin/env python3
"""Validate the fixed setup-readiness report contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


SECTIONS = (
    "Summary",
    "Skills you can use",
    "Access and data",
    "Contract checks",
    "Try next",
    "Appendix A — Sources",
)
TILES = ("Skills ready", "Partial", "Not licensed", "Checks passed")


def validate(report: object) -> list[str]:
    if not isinstance(report, dict):
        return ["report root must be an object"]
    errors: list[str] = []
    meta = report.get("meta")
    executive = report.get("executive")
    sections = report.get("sections")
    if not isinstance(meta, dict):
        errors.append("meta must be an object")
    else:
        for field in ("title", "eyebrow", "header_label", "data_as_of", "signal", "completeness"):
            if not meta.get(field):
                errors.append(f"meta.{field} is required")
    if not isinstance(executive, dict):
        errors.append("executive must be an object")
    else:
        if re.search(r"\[S\d+\]", str(executive.get("bottom_line", ""))) is None:
            errors.append("executive.bottom_line must cite [S#]")
        labels = [
            tile.get("label")
            for tile in executive.get("tiles", [])
            if isinstance(tile, dict)
        ]
        if labels != list(TILES):
            errors.append("executive tiles must retain the four readiness labels")
    if not isinstance(sections, list):
        return errors + ["sections must be an array"]
    titles = [section.get("title") for section in sections if isinstance(section, dict)]
    if titles != list(SECTIONS):
        errors.append("setup sections must retain exact order")
    required_types = {
        "Access and data": {"kv", "coverage"},
        "Contract checks": {"table"},
        "Try next": {"questions"},
        "Appendix A — Sources": {"table"},
    }
    for section in sections:
        if not isinstance(section, dict):
            continue
        expected = required_types.get(str(section.get("title")))
        if expected is None:
            continue
        actual = {
            block.get("type")
            for block in section.get("blocks", [])
            if isinstance(block, dict)
        }
        if not expected <= actual:
            errors.append(f"{section.get('title')} is missing required block types")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <report.json>")
        return 2
    try:
        report = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR — {error}")
        return 2
    errors = validate(report)
    if errors:
        for error in errors:
            print(f"FAIL — {error}")
        return 1
    print("PASS — setup readiness report contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
