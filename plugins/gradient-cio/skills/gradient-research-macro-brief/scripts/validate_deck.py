#!/usr/bin/env python3
"""Validate the fixed macro-briefing deck contract."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


TITLE_PATTERNS = (
    r".+",
    r"Rates\b",
    r"Risk posture\b",
    r"Positioning\b",
    r"What supports risk and what detracts\b",
    r"What would confirm or break the thesis\b",
    r"A crowded window\b",
    r"10-year assumptions\b",
    r"Questions for the committee\b",
    r"Sources, data quality and limits",
)


def validate(deck: object) -> list[str]:
    if not isinstance(deck, dict):
        return ["deck root must be an object"]
    errors: list[str] = []
    meta = deck.get("meta")
    slides = deck.get("slides")
    if not isinstance(meta, dict):
        errors.append("meta must be an object")
    else:
        for field in ("title", "header_label", "data_as_of"):
            if not meta.get(field):
                errors.append(f"meta.{field} is required")
    if not isinstance(slides, list):
        return errors + ["slides must be an array"]
    if len(slides) != 10:
        errors.append("macro briefing must contain exactly 10 slides")
    for index, slide in enumerate(slides, start=1):
        if not isinstance(slide, dict):
            errors.append(f"slide {index} must be an object")
            continue
        title = str(slide.get("title", "")).strip()
        if not title:
            errors.append(f"slide {index} title is required")
        elif index <= len(TITLE_PATTERNS) and re.match(
            TITLE_PATTERNS[index - 1],
            title,
            re.IGNORECASE,
        ) is None:
            errors.append(f"slide {index} is out of the fixed macro-brief order")
        evidence_blocks = []
        for field in ("blocks", "left", "right"):
            value = slide.get(field)
            if isinstance(value, list):
                evidence_blocks.extend(value)
        if not evidence_blocks:
            errors.append(f"slide {index} requires evidence blocks")
    if slides and isinstance(slides[-1], dict):
        if slides[-1].get("title") != "Sources, data quality and limits":
            errors.append("final slide must be Sources, data quality and limits")
    text = json.dumps(deck, ensure_ascii=False)
    if re.search(r"<[^<>\n]{2,100}>|\b(?:TBD|TODO|FIXME|TK)\b", text):
        errors.append("deck contains an unresolved placeholder")
    if re.search(r"\[S\d+\]", text) is None:
        errors.append("deck requires source tags")
    return errors


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(f"usage: {Path(argv[0]).name} <deck.json>")
        return 2
    try:
        deck = json.loads(Path(argv[1]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"ERROR — {error}")
        return 2
    errors = validate(deck)
    if errors:
        for error in errors:
            print(f"FAIL — {error}")
        return 1
    print("PASS — macro briefing deck contract is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
