#!/usr/bin/env python3
"""Validate the common evidence and handoff contract for IDD reports."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from validate_handoff import validate_handoff

SOURCE_TAG = re.compile(r"\[S[0-9]+\]")


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in _strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _strings(item)]
    return []


def validate_report(report: Any) -> list[str]:
    """Return common IDD report contract errors."""
    if not isinstance(report, dict):
        return ["report must be an object"]
    errors: list[str] = []
    meta = report.get("meta")
    if not isinstance(meta, dict):
        return ["meta must be an object"]
    for field in ("title", "eyebrow", "header_label", "running_head", "data_as_of"):
        if not isinstance(meta.get(field), str) or not meta[field].strip():
            errors.append(f"meta.{field} is required")
    errors.extend(
        f"meta.handoff: {error}"
        for error in validate_handoff(meta.get("handoff"))
    )
    sections = report.get("sections")
    if not isinstance(sections, list) or len(sections) < 5:
        errors.append("sections must contain at least five report sections")
        return errors
    titles = [
        section.get("title", "")
        for section in sections
        if isinstance(section, dict)
    ]
    if not any("executive" in str(title).casefold() for title in titles):
        errors.append("an Executive section is required")
    if not any("coverage" in str(title).casefold() for title in titles):
        errors.append("a coverage section is required")
    if not any(
        "sources" in str(title).casefold() and "method" in str(title).casefold()
        for title in titles
    ):
        errors.append("a Sources and methods appendix is required")
    analytical_text = "\n".join(_strings(sections[:-1]))
    if SOURCE_TAG.search(analytical_text) is None:
        errors.append("analytical sections require at least one [S#] source tag")
    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_idd_report.py <report.json>", file=sys.stderr)
        return 2
    try:
        report = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR — {error}", file=sys.stderr)
        return 2
    errors = validate_report(report)
    if errors:
        for error in errors:
            print(f"FAIL — {error}", file=sys.stderr)
        return 1
    print("PASS — IDD report contract valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
