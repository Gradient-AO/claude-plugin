#!/usr/bin/env python3
"""Validate and compose an IC memo JSON report.

Usage:
  python compose_memo_json.py memo.md visuals.json meta.json memo.json

The markdown must already pass validate_memo.py. This command validates the
separate visual and analysis layer, then atomically writes a JSON-block report.
Exit code 0 = pass, 1 = invalid content, 2 = invalid invocation or unreadable input.
"""

from __future__ import annotations

import copy
import json
import math
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gradient_report import md_document_to_report  # noqa: E402


TAG = re.compile(r"\[S(\d+)\]")
PLACEHOLDER = re.compile(r"<[^<>\n]{2,80}>")
ALLOWED_TONES = {"info", "watch", "bad", "good"}
ANALYSIS_SECTIONS = {"2", "3", "4", "5", "6", "7", "9", "10", "12", "13"}
NEW_PAGE_NUMBERS = {"05", "07", "14"}
PROHIBITED_ANALYSIS_ACTIONS = [
    r"\bwe recommend\b",
    r"\bthe committee should\b",
    r"\bthe committee must\b",
    r"\bthe committee is asked to\b",
]
ANALYSIS_LABELS = (
    "Observation:",
    "Why it matters:",
    "Uncertainty:",
    "What would change the view:",
)
VISUAL_TYPES = {
    "chart",
    "line",
    "bars",
    "percentiles",
    "waterfall",
    "band",
    "stacked",
    "heat",
    "tiles",
    "coverage",
    "findings",
}
EXECUTIVE_TILE_LABELS = [
    "Trailing 1Y vs benchmark",
    "IPS breaches",
    "Expected return vs objective",
    "T1 liquidity",
]
REQUIRED_SLOTS: dict[str, list[tuple[str, str]]] = {
    "1": [("statement", "Recommendation")],
    "3": [
        ("bars", "Current weight by asset class"),
        ("bars", "Active weight vs policy (bps)"),
    ],
    "4": [
        ("coverage", "Policy constraint status"),
        ("bars", "Concentration vs limit"),
    ],
    "5": [
        ("line", "Growth of 100"),
        ("bars", "Calendar-year returns"),
        ("bars", "1Y attribution — total effect by asset class (bps)"),
    ],
    "6": [("chart", "Factor and currency exposure")],
    "7": [
        ("bars", "Gradient vs consensus gap (bps)"),
        ("tiles", "Forward context"),
    ],
    "9": [
        ("bars", "Liquidity tiers (% NAV)"),
        ("chart", "commitments-liquidity-scorecard"),
        ("chart", "commitments-pacing"),
        ("chart", "commitments-cashflow"),
    ],
    "10": [("findings", "Exposure-weighted diligence findings")],
    "12": [("tiles", "Macro readings")],
    "14": [("tiles", "Risk count by rating")],
}


def collect_strings(value: Any) -> list[str]:
    """Return every string nested in a JSON-compatible value."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in collect_strings(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in collect_strings(item)]
    return []


def nested_blocks(blocks: list[Any]) -> list[dict[str, Any]]:
    """Flatten report blocks, including both sides of two-column layouts."""
    found: list[dict[str, Any]] = []
    for value in blocks:
        if not isinstance(value, dict):
            continue
        found.append(value)
        if value.get("type") == "two_col":
            for side in ("left", "right"):
                child = value.get(side, [])
                if isinstance(child, list):
                    found.extend(nested_blocks(child))
    return found


def block_identity(block: dict[str, Any]) -> str:
    """Return the title or chart identifier used to match a semantic slot."""
    if block.get("type") == "chart":
        chart = block.get("chart")
        if isinstance(chart, dict):
            return " ".join(
                str(chart.get(field, ""))
                for field in ("chart_id", "id", "title")
            )
    return str(block.get("title", ""))


def unavailable_for(blocks: list[dict[str, Any]], title: str) -> bool:
    """Return whether a specific required slot has a reasoned unavailable callout."""
    title_lower = title.lower()
    for block in blocks:
        if block.get("type") != "callout" or block.get("tone") != "watch":
            continue
        identity = str(block.get("title", "")).lower()
        text = str(block.get("text", ""))
        if title_lower in identity and re.match(r"^Not available — \S", text):
            return True
    return False


def validate_slots(section: str, blocks: list[dict[str, Any]], errors: list[str]) -> None:
    """Validate required visual types and semantic titles for one section."""
    for block_type, title in REQUIRED_SLOTS.get(section, []):
        matched = any(
            block.get("type") == block_type
            and title.lower() in block_identity(block).lower()
            for block in blocks
        )
        if not matched and not unavailable_for(blocks, title):
            errors.append(
                f"Section {section}: missing {block_type} slot '{title}' "
                "or its titled Not available callout"
            )


def validate_bars(blocks: list[dict[str, Any]], section: str, errors: list[str]) -> None:
    """Validate finite signed bar values."""
    for block in blocks:
        if block.get("type") != "bars":
            continue
        for item in block.get("items", []):
            if not isinstance(item, dict):
                errors.append(f"Section {section}: bars item must be an object")
                continue
            value = item.get("value")
            if (
                not isinstance(value, (int, float))
                or isinstance(value, bool)
                or not math.isfinite(value)
            ):
                errors.append(
                    f"Section {section}: bars item value must be a finite signed number"
                )
                continue
            display = str(item.get("display", "")).strip()
            if display.startswith(("-", "−")) and item.get("color") != "#E8735A":
                errors.append(
                    f"Section {section}: negative display '{display}' must use coral #E8735A"
                )
            if display.startswith("+") and item.get("color") != "#B5E52A":
                errors.append(
                    f"Section {section}: positive display '{display}' must use lime #B5E52A"
                )


def validate_analysis(
    section: str,
    analysis: Any,
    errors: list[str],
) -> None:
    """Validate callout counts, evidence tags, lengths, and tone vocabulary."""
    if not isinstance(analysis, list):
        errors.append(f"Section {section}: analysis must be an array")
        return
    minimum = 3 if section == "2" else 1
    maximum = 5 if section == "2" else 3
    if not minimum <= len(analysis) <= maximum:
        errors.append(
            f"Section {section}: needs {minimum}–{maximum} analysis callouts "
            f"(found {len(analysis)})"
        )
    for index, callout in enumerate(analysis, start=1):
        if not isinstance(callout, dict):
            errors.append(f"Section {section}: analysis {index} must be an object")
            continue
        title = str(callout.get("title", "")).strip()
        text = str(callout.get("text", "")).strip()
        tone = callout.get("tone", "info")
        if not title:
            errors.append(f"Section {section}: analysis {index} has no title")
        elif len(title.split()) > 6:
            errors.append(f"Section {section}: analysis title exceeds six words: '{title}'")
        if not TAG.search(text):
            errors.append(f"Section {section}: analysis '{title}' cites no [S#]")
        if len(text.split()) > 60:
            errors.append(f"Section {section}: analysis '{title}' exceeds 60 words")
        normalized = text.replace("**", "")
        positions = [normalized.find(label) for label in ANALYSIS_LABELS]
        if any(position < 0 for position in positions) or positions != sorted(positions):
            errors.append(
                f"Section {section}: analysis '{title}' must use Observation, "
                "Why it matters, Uncertainty, and What would change the view in order"
            )
        if tone not in ALLOWED_TONES:
            errors.append(f"Section {section}: analysis '{title}' has invalid tone '{tone}'")
        for pattern in PROHIBITED_ANALYSIS_ACTIONS:
            if re.search(pattern, text, re.IGNORECASE):
                errors.append(
                    f"Section {section}: analysis '{title}' introduces decision language; "
                    "keep the action in Section 1"
                )
                break


def validate_flow(
    section: str,
    before: list[Any],
    after: list[Any],
    markdown_has_table: bool,
    errors: list[str],
) -> None:
    """Require evidence-first flow and reject table walls in nested block lists."""
    before_blocks = nested_blocks(before)
    if section in ANALYSIS_SECTIONS and markdown_has_table and not any(
        block.get("type") in VISUAL_TYPES
        or (
            block.get("type") in {"callout", "unavailable"}
            and re.search(r"\bNot (?:available|applicable) — \S", " ".join(collect_strings(block)))
        )
        for block in before_blocks
    ):
        errors.append(
            f"Section {section}: before must start the analytical flow with a "
            "visual or typed unavailable block"
        )

    def check_list(values: list[Any], location: str) -> None:
        consecutive = 0
        for index, value in enumerate(values):
            if not isinstance(value, dict):
                continue
            consecutive = consecutive + 1 if value.get("type") == "table" else 0
            if consecutive > 2:
                errors.append(
                    f"Section {section}: {location} has more than two consecutive "
                    f"tables at block {index + 1}"
                )
            if value.get("type") == "two_col":
                for side in ("left", "right"):
                    children = value.get(side, [])
                    if isinstance(children, list):
                        check_list(children, f"{location}.{side}")

    check_list(before, "before")
    check_list(after, "after")


def validate_inputs(
    markdown: str,
    visuals: Any,
    meta: Any,
) -> list[str]:
    """Return all visual-layer validation failures."""
    errors: list[str] = []
    if not isinstance(visuals, dict):
        return ["visuals.json root must be an object"]
    if not isinstance(meta, dict):
        return ["meta.json root must be an object"]

    appendix_match = re.search(
        r"^## Appendix A\b(.*?)(?=^## Appendix B\b)",
        markdown,
        re.MULTILINE | re.DOTALL,
    )
    appendix = appendix_match.group(1) if appendix_match else ""
    known_tags = set(re.findall(r"^\|\s*S(\d+)\s*\|", appendix, re.MULTILINE))
    if not known_tags:
        errors.append("Appendix A contains no source rows")

    executive = meta.get("executive")
    if not isinstance(executive, dict):
        errors.append("meta.executive must be an object")
    else:
        tiles = executive.get("tiles")
        if not isinstance(tiles, list) or len(tiles) != 4:
            errors.append("meta.executive.tiles must contain exactly four tiles")
        else:
            labels = [str(tile.get("label", "")) for tile in tiles if isinstance(tile, dict)]
            if labels != EXECUTIVE_TILE_LABELS:
                errors.append(
                    "meta.executive.tiles labels must be, in order: "
                    + ", ".join(EXECUTIVE_TILE_LABELS)
                )
            for tile in tiles:
                if not isinstance(tile, dict):
                    errors.append("Every executive tile must be an object")
                    continue
                if not TAG.search(" ".join(collect_strings(tile))):
                    errors.append(
                        f"Executive tile '{tile.get('label', '')}' must cite at least one [S#]"
                    )

    for section in ANALYSIS_SECTIONS | set(REQUIRED_SLOTS) | {"13"}:
        value = visuals.get(section)
        if not isinstance(value, dict):
            errors.append(f"Section {section}: missing visual-layer object")
            continue
        before = value.get("before", [])
        after = value.get("after", [])
        if not isinstance(before, list) or not isinstance(after, list):
            errors.append(f"Section {section}: before and after must be arrays")
            continue
        blocks = nested_blocks(before + after)
        validate_slots(section, blocks, errors)
        validate_bars(blocks, section, errors)
        section_match = re.search(
            rf"^## {re.escape(section)}\..*?(?=^## |\Z)",
            markdown,
            re.MULTILINE | re.DOTALL,
        )
        markdown_has_table = bool(
            section_match
            and re.search(r"^\s*\|", section_match.group(0), re.MULTILINE)
        )
        validate_flow(section, before, after, markdown_has_table, errors)
        if section in ANALYSIS_SECTIONS:
            validate_analysis(section, value.get("analysis"), errors)

    section_13 = visuals.get("13")
    if isinstance(section_13, dict):
        blocks_13 = nested_blocks(
            list(section_13.get("before", [])) + list(section_13.get("after", []))
        )
        has_change = any(block.get("type") == "two_col" for block in blocks_13)
        has_no_change = any(
            block.get("type") == "callout"
            and block.get("title") == "No change proposed"
            for block in blocks_13
        )
        if not (has_change or has_no_change):
            errors.append(
                "Section 13: requires a Current vs proposed two_col or "
                "'No change proposed' callout"
            )

    unknown_keys = set(visuals) - {str(number) for number in range(1, 17)}
    if unknown_keys:
        errors.append("Unknown visuals.json section keys: " + ", ".join(sorted(unknown_keys)))

    all_text = "\n".join(collect_strings([visuals, meta]))
    missing_tags = set(TAG.findall(all_text)) - known_tags
    if missing_tags:
        errors.append(
            "Tags not in Appendix A: "
            + ", ".join(f"S{tag}" for tag in sorted(missing_tags, key=int))
        )
    placeholders = PLACEHOLDER.findall(all_text)
    if placeholders:
        errors.append("Unresolved placeholder in visual layer: " + placeholders[0])
    return errors


def compose(markdown: str, visuals: dict[str, Any], meta: dict[str, Any]) -> dict[str, Any]:
    """Merge validated markdown, visuals, and metadata into a report document."""
    report = md_document_to_report(markdown, copy.deepcopy(meta))
    for section in report["sections"]:
        number = str(section.get("num", ""))
        if number in NEW_PAGE_NUMBERS:
            section["new_page"] = True
        if not number.isdigit():
            continue
        visual = visuals.get(str(int(number)))
        if not isinstance(visual, dict):
            continue
        markdown_blocks = section.get("blocks", [])
        analysis = [
            {
                "type": "callout",
                "role": (
                    "key_judgment"
                    if str(int(number)) == "2"
                    else "analysis"
                ),
                "tone": callout.get("tone", "info"),
                "title": (
                    f"Key judgment — {callout['title']}"
                    if str(int(number)) == "2"
                    else f"Analysis — {callout['title']}"
                ),
                "text": callout["text"],
            }
            for callout in visual.get("analysis", [])
        ]
        if not markdown_blocks:
            section["blocks"] = visual.get("before", []) + visual.get("after", []) + analysis
            continue
        first = markdown_blocks[0]
        text = str(first.get("text", ""))
        opening, separator, remainder = text.partition("\n\n")
        section["blocks"] = (
            [{"type": "markdown", "text": opening}]
            + visual.get("before", [])
            + ([{"type": "markdown", "text": remainder}] if separator else [])
            + markdown_blocks[1:]
            + visual.get("after", [])
            + analysis
        )
    return report


def load_json(path: Path) -> Any:
    """Read one JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))


def write_atomic(path: Path, document: dict[str, Any]) -> None:
    """Atomically replace the output only after all validation succeeds."""
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(document, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temporary_name, path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def main() -> int:
    """Run the command-line composer."""
    if len(sys.argv) != 5:
        print(__doc__)
        return 2
    markdown_path, visuals_path, meta_path, output_path = map(Path, sys.argv[1:])
    try:
        markdown = markdown_path.read_text(encoding="utf-8")
        visuals = load_json(visuals_path)
        meta = load_json(meta_path)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Unable to read composition inputs: {error}")
        return 2

    errors = validate_inputs(markdown, visuals, meta)
    if errors:
        print(f"FAIL — {len(errors)} issue(s):")
        for error in errors:
            print(f"  - {error}")
        return 1

    report = compose(markdown, visuals, meta)
    try:
        write_atomic(output_path, report)
    except OSError as error:
        print(f"Unable to write {output_path}: {error}")
        return 2
    print(f"PASS — wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
