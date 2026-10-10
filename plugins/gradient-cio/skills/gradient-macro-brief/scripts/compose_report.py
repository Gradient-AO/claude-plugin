#!/usr/bin/env python3
"""Compose validated markdown, visual blocks and metadata into report.json.

Usage:
  python compose_report.py document.md visuals.json meta.json report.json

Placements may be keyed by a section number (``"3"``), source heading, or
display title. A visual file can use ``{"sections": {...}}`` or place section
keys at its root. Each placement supports ``before``, ``after`` and ``analysis``.
"""

from __future__ import annotations

import copy
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

from gradient_report import md_document_to_report


SOURCE_TAG = re.compile(r"\[S(\d+)\]")
PLACEHOLDER = re.compile(
    r"<[^<>\n]{2,100}>|\{\{[^{}\n]+\}\}|\b(?:TBD|TODO|FIXME|TK)\b",
    re.IGNORECASE,
)


def collect_strings(value: Any) -> list[str]:
    """Return every nested string."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in collect_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in collect_strings(item)]
    return []


def normalize_unavailable(block: dict[str, Any]) -> dict[str, Any]:
    """Convert the compose-layer unavailable shorthand to a report callout."""
    if block.get("type") == "unavailable":
        tags = " ".join(f"[{tag}]" for tag in block.get("source_tags", []))
        return {
            "type": "callout",
            "role": "unavailable",
            "tone": "info",
            "title": block.get("title", "Unavailable"),
            "text": f"Not available — {block.get('reason', 'reason not supplied')} {tags}".strip(),
        }
    result = copy.deepcopy(block)
    if result.get("type") == "two_col":
        result["left"] = [
            normalize_unavailable(child) for child in result.get("left", [])
        ]
        result["right"] = [
            normalize_unavailable(child) for child in result.get("right", [])
        ]
    return result


def validate_inputs(
    markdown: str, visuals: Any, meta: Any
) -> list[str]:
    """Validate generic composition invariants without replacing skill validators."""
    errors: list[str] = []
    if not isinstance(visuals, dict):
        return ["visuals.json root must be an object"]
    if not isinstance(meta, dict):
        return ["meta.json root must be an object"]
    if not re.search(r"^#\s+\S", markdown, re.MULTILINE):
        errors.append("markdown needs a level-one title")
    if not re.search(r"^##\s+\S", markdown, re.MULTILINE):
        errors.append("markdown needs at least one level-two section")
    all_text = "\n".join(collect_strings([visuals, meta]))
    placeholder = PLACEHOLDER.search(all_text)
    if placeholder:
        errors.append(f"unresolved placeholder: {placeholder.group(0)}")
    appendix_tags = set(
        re.findall(r"^\|\s*S(\d+)\s*\|", markdown, re.MULTILINE)
    )
    referenced = set(SOURCE_TAG.findall(all_text))
    if appendix_tags:
        for tag in sorted(referenced - appendix_tags, key=int):
            errors.append(f"[S{tag}] is missing from the markdown sources appendix")
    return errors


def placement_map(visuals: dict[str, Any]) -> dict[str, Any]:
    """Return section placement entries, excluding visual-file metadata."""
    source = visuals.get("sections", visuals)
    if not isinstance(source, dict):
        return {}
    return {
        str(key): value
        for key, value in source.items()
        if key not in {"schema_version", "executive_tiles", "required_slots"}
        and isinstance(value, dict)
    }


def placement_for(
    section: dict[str, Any], placements: dict[str, Any]
) -> dict[str, Any]:
    """Find a placement by normalized number or title."""
    candidates = [
        str(section.get("num", "")),
        str(int(section["num"])) if str(section.get("num", "")).isdigit() else "",
        str(section.get("source_heading", "")),
        str(section.get("title", "")),
    ]
    for candidate in candidates:
        if candidate and candidate in placements:
            return placements[candidate]
    display_title = str(section.get("title", "")).strip().casefold()
    for key, value in placements.items():
        normalized = re.sub(
            r"^(?:\d+\.\s+|Appendix\s+[A-Z]\b\s*[—–:-]?\s*)",
            "",
            key,
        ).strip().casefold()
        if normalized == display_title or (
            str(section.get("num", "")).isalpha()
            and display_title.startswith("appendix")
            and key.casefold().startswith(f"appendix {str(section['num']).casefold()}")
        ):
            return value
    return {}


def analysis_blocks(value: Any, key_judgments: bool = False) -> list[dict[str, Any]]:
    """Normalize concise analysis records to renderer callouts."""
    if not isinstance(value, list):
        return []
    blocks: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        prefix = "Key judgment" if key_judgments else "Analysis"
        blocks.append(
            {
                "type": "callout",
                "role": "analysis",
                "tone": item.get("tone", "info"),
                "title": title if title.startswith(prefix) else f"{prefix} — {title}",
                "text": item.get("text", ""),
            }
        )
    return blocks


def compose(
    markdown: str, visuals: dict[str, Any], meta: dict[str, Any]
) -> dict[str, Any]:
    """Merge source layers without rewriting authoritative markdown."""
    report = md_document_to_report(markdown, copy.deepcopy(meta))
    placements = placement_map(visuals)
    for section in report["sections"]:
        placement = placement_for(section, placements)
        before = [
            normalize_unavailable(block)
            for block in placement.get("before", [])
            if isinstance(block, dict)
        ]
        after = [
            normalize_unavailable(block)
            for block in placement.get("after", [])
            if isinstance(block, dict)
        ]
        analysis = analysis_blocks(
            placement.get("analysis"),
            key_judgments=str(section.get("num", "")).lstrip("0") == "2",
        )
        markdown_blocks = section.get("blocks", [])
        section["blocks"] = before + markdown_blocks + after + analysis
    executive_tiles = visuals.get("executive_tiles")
    if executive_tiles is not None:
        report.setdefault("executive", {})["tiles"] = executive_tiles
    return report


def write_atomic(path: Path, document: dict[str, Any]) -> None:
    """Write only a fully composed JSON document."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, text=True
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    """Run the generic composer."""
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    markdown_path, visuals_path, meta_path, output_path = map(Path, sys.argv[1:])
    try:
        markdown = markdown_path.read_text(encoding="utf-8")
        visuals = json.loads(visuals_path.read_text(encoding="utf-8"))
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR — unable to load composition inputs: {error}")
        return 2
    errors = validate_inputs(markdown, visuals, meta)
    if errors:
        print(f"FAIL — {len(errors)} composition issue(s)")
        for error in errors:
            print(f"  - {error}")
        return 1
    write_atomic(output_path, compose(markdown, visuals, meta))
    print(f"PASS — wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
