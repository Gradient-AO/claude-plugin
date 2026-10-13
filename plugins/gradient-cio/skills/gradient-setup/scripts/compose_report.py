#!/usr/bin/env python3
"""Compose validated markdown, visual blocks and metadata into report.json.

Usage:
  python compose_report.py document.md visuals.json meta.json report.json

Placements may be keyed by a section number (``"3"``), source heading, or
display title. A visual file can use ``{"sections": {...}}`` or place section
keys at its root. Each placement supports ``before``, ``after`` and ``analysis``.

Saved JSON tool responses can feed an ordinary line block without local
calculation. Add ``series_imports`` to the line block, with one directive per
series::

    {
      "type": "line",
      "title": "Returned series",
      "series_imports": [{
        "name": "Portfolio",
        "source_file": "responses/returns.json",
        "row_path": "data.points",
        "x_field": "date",
        "y_field": "portfolio"
      }]
    }

Relative source files resolve first beside the visual file and then from the
current invocation directory. Imported x/y values are copied verbatim. The
composer does not calculate returns, effects, differences or indexes.
"""

from __future__ import annotations

import copy
import argparse
import json
import math
import os
import re
import tempfile
from pathlib import Path
from typing import Any

from gradient_report import md_document_to_report
from report_layout import load_layout_budget, validate_report_budget


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
        normalized = {
            "type": "callout",
            "role": "unavailable",
            "tone": "info",
            "title": block.get("title", "Unavailable"),
            "text": f"Not available — {block.get('reason', 'reason not supplied')} {tags}".strip(),
        }
        if "unavailable_for" in block:
            normalized["unavailable_for"] = copy.deepcopy(block["unavailable_for"])
        return normalized
    result = copy.deepcopy(block)
    if result.get("type") == "two_col":
        result["left"] = [
            normalize_unavailable(child) for child in result.get("left", [])
        ]
        result["right"] = [
            normalize_unavailable(child) for child in result.get("right", [])
        ]
    return result


def _mapped_value(value: Any, path: str, label: str) -> Any:
    """Resolve a dot-separated object path with deterministic failures."""
    if not isinstance(path, str) or not path.strip():
        raise ValueError(f"{label} must be a non-empty dot-separated path")
    current = value
    for component in path.split("."):
        if not component or not isinstance(current, dict) or component not in current:
            raise ValueError(f"{label} path '{path}' is missing component '{component}'")
        current = current[component]
    return current


def _source_path(
    source_file: str,
    visual_path: Path | None,
    invocation_dir: Path | None,
) -> Path:
    """Resolve one saved response beside visuals, then from the invocation."""
    source = Path(source_file)
    if source.is_absolute():
        candidates = [source]
    else:
        candidates = []
        if visual_path is not None:
            candidates.append(visual_path.resolve().parent / source)
        candidates.append((invocation_dir or Path.cwd()).resolve() / source)
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    searched = ", ".join(str(candidate) for candidate in candidates)
    raise ValueError(f"direct-series source_file '{source_file}' was not found ({searched})")


def import_direct_series(
    directive: dict[str, Any],
    visual_path: Path | None = None,
    invocation_dir: Path | None = None,
) -> dict[str, Any]:
    """Load one returned x/y series without transforming either value."""
    required = ("name", "source_file", "row_path", "x_field", "y_field")
    missing = [field for field in required if not directive.get(field)]
    if missing:
        raise ValueError(
            "direct-series directive is missing required field(s): "
            + ", ".join(missing)
        )
    source_path = _source_path(
        str(directive["source_file"]),
        visual_path,
        invocation_dir,
    )
    try:
        payload = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"unable to load direct-series source '{source_path}': {error}"
        ) from error
    rows = _mapped_value(payload, str(directive["row_path"]), "row_path")
    if not isinstance(rows, list) or not rows:
        raise ValueError("direct-series row_path must resolve to a non-empty array")
    points: list[list[Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"direct-series row {index} must be an object")
        x_value = _mapped_value(row, str(directive["x_field"]), "x_field")
        y_value = _mapped_value(row, str(directive["y_field"]), "y_field")
        if (
            not isinstance(x_value, (str, int, float))
            or isinstance(x_value, bool)
            or not isinstance(y_value, (int, float))
            or isinstance(y_value, bool)
            or not math.isfinite(float(y_value))
        ):
            raise ValueError(
                f"direct-series row {index} requires scalar x and finite numeric y values"
            )
        points.append([x_value, y_value])
    series = {"name": str(directive["name"]), "points": points}
    for optional in ("color", "dash"):
        if optional in directive:
            series[optional] = copy.deepcopy(directive[optional])
    return series


def resolve_direct_series_imports(
    value: Any,
    visual_path: Path | None = None,
    invocation_dir: Path | None = None,
) -> Any:
    """Replace line ``series_imports`` directives recursively."""
    if isinstance(value, list):
        return [
            resolve_direct_series_imports(item, visual_path, invocation_dir)
            for item in value
        ]
    if not isinstance(value, dict):
        return copy.deepcopy(value)
    result = {
        key: resolve_direct_series_imports(item, visual_path, invocation_dir)
        for key, item in value.items()
        if key != "series_imports"
    }
    if "series_imports" not in value:
        return result
    if value.get("type") != "line":
        raise ValueError("series_imports is permitted only on line blocks")
    if "series" in value:
        raise ValueError("line blocks cannot combine series and series_imports")
    directives = value["series_imports"]
    if (
        not isinstance(directives, list)
        or not directives
        or not all(isinstance(item, dict) for item in directives)
    ):
        raise ValueError("series_imports must be a non-empty array of objects")
    result["series"] = [
        import_direct_series(item, visual_path, invocation_dir)
        for item in directives
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
    markdown: str,
    visuals: dict[str, Any],
    meta: dict[str, Any],
    visual_path: Path | None = None,
    invocation_dir: Path | None = None,
) -> dict[str, Any]:
    """Merge source layers without rewriting authoritative markdown."""
    visuals = resolve_direct_series_imports(
        visuals,
        visual_path=visual_path,
        invocation_dir=invocation_dir,
    )
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=Path)
    parser.add_argument("visuals", type=Path)
    parser.add_argument("meta", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--budget", type=Path)
    args = parser.parse_args()
    markdown_path = args.markdown
    visuals_path = args.visuals
    meta_path = args.meta
    output_path = args.output
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
    try:
        report = compose(
            markdown,
            visuals,
            meta,
            visual_path=visuals_path,
            invocation_dir=Path.cwd(),
        )
    except ValueError as error:
        print(f"FAIL — composition issue: {error}")
        return 1
    if args.budget:
        try:
            budget = load_layout_budget(args.budget)
        except ValueError as error:
            print(f"ERROR — unable to load layout budget: {error}")
            return 2
        budget_errors = validate_report_budget(report, budget)
        if budget_errors:
            print(f"FAIL — {len(budget_errors)} content budget issue(s)")
            for error in budget_errors:
                print(f"  - {error}")
            return 1
    write_atomic(output_path, report)
    print(f"PASS — wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
