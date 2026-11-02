#!/usr/bin/env python3
"""Reject report-skill tool references outside the shipped MCP catalog."""

from __future__ import annotations

import json
import pathlib
import re
import sys


ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "shared" / "public-tools.json"
TOOL_TOKEN = re.compile(
    r"\b(?:analyze|build|check|commit|compare|confirm|create|get|list|preview|"
    r"resolve|rollback|run|save|screen|search|stage|start|update|upload)"
    r"_[a-z0-9_]+\b"
)
BACKTICK_OR_CALL = re.compile(
    rf"`({TOOL_TOKEN.pattern})`|({TOOL_TOKEN.pattern})\s*\(",
)


def scanned_paths() -> list[pathlib.Path]:
    """Return the public guidance files that are allowed to name tools."""
    skills = ROOT / "skills"
    return sorted(
        [
            *skills.glob("*/SKILL.md"),
            *skills.glob("*/references/data-map.md"),
            *skills.glob("*/references/modes/*-data-map.md"),
        ]
    )


def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    tools = set(catalog.get("tools", []))
    failures: list[str] = []
    for path in scanned_paths():
        text = path.read_text(encoding="utf-8")
        for match in BACKTICK_OR_CALL.finditer(text):
            name = match.group(1) or match.group(2)
            if name.count("_") < 2 and name not in tools:
                continue
            if name not in tools:
                line = text.count("\n", 0, match.start()) + 1
                failures.append(
                    f"{path.relative_to(ROOT)}:{line}: unknown MCP tool {name}"
                )
    if failures:
        print("\n".join(f"FAIL — {failure}" for failure in failures), file=sys.stderr)
        return 1
    print(f"tool references match {len(tools)} cataloged MCP tools")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
