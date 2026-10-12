#!/usr/bin/env python3
"""Canonical schema-v2 validation and mode resolution for layout budgets."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 2
DESIGN_PROFILES = frozenset({"analytical", "reference", "deck"})
SECTION_ROLES = frozenset(
    {"summary", "analytical", "list", "closing", "appendix", "reference"}
)
SELECTOR_PATHS = frozenset({"meta.mode", "meta.week_kind"})
SECTION_LIMIT_FIELDS = frozenset(
    {
        "max_words",
        "max_body_table_rows",
        "max_table_rows",
        "max_visuals",
        "hard_max_pdf_pages",
        "max_pages",
    }
)
ROOT_FIELDS = frozenset(
    {
        "schema_version",
        "design_profile",
        "forced_breaks",
        "pdf",
        "pptx",
        "content",
        "selector",
        "modes",
    }
)
MODE_FIELDS = frozenset({"forced_breaks", "pdf", "pptx", "content"})
PDF_FIELDS = frozenset(
    {
        "target_pages",
        "hard_max_pages",
        "minimum_body_fill",
        "orphan_tail_max_fill",
    }
)
PPTX_FIELDS = frozenset({"target_slides", "hard_max_slides"})
CANONICAL_MINIMUM_BODY_FILL = 0.40
CANONICAL_ORPHAN_TAIL_MAX_FILL = 0.20


class LayoutBudgetSchemaError(ValueError):
    """Raised when a layout budget cannot be loaded or resolved."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("\n".join(errors))
        self.errors = errors


def _nonnegative_integer(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _validate_range(
    value: Any,
    location: str,
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location} must be an object")
        return
    unknown = sorted(set(value) - {"min", "max"})
    if unknown:
        errors.append(f"{location} has unknown field(s): {', '.join(unknown)}")
    if set(value) != {"min", "max"}:
        errors.append(f"{location} must contain exactly min and max")
        return
    minimum, maximum = value["min"], value["max"]
    if not _nonnegative_integer(minimum) or not _nonnegative_integer(maximum):
        errors.append(f"{location}.min/max must be nonnegative integers")
    elif minimum > maximum:
        errors.append(f"{location}.min cannot exceed max")


def _validate_pdf(value: Any, location: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location} must be an object")
        return
    unknown = sorted(set(value) - PDF_FIELDS)
    if unknown:
        errors.append(f"{location} has unknown field(s): {', '.join(unknown)}")
    missing = sorted(PDF_FIELDS - set(value))
    if missing:
        errors.append(f"{location} is missing field(s): {', '.join(missing)}")
    if "target_pages" in value:
        _validate_range(value["target_pages"], f"{location}.target_pages", errors)
    if "hard_max_pages" in value and not _nonnegative_integer(
        value["hard_max_pages"]
    ):
        errors.append(f"{location}.hard_max_pages must be a nonnegative integer")
    if (
        value.get("minimum_body_fill") is not None
        and value.get("minimum_body_fill") != CANONICAL_MINIMUM_BODY_FILL
    ):
        errors.append(
            f"{location}.minimum_body_fill must be "
            f"{CANONICAL_MINIMUM_BODY_FILL:.2f}"
        )
    if (
        value.get("orphan_tail_max_fill") is not None
        and value.get("orphan_tail_max_fill") != CANONICAL_ORPHAN_TAIL_MAX_FILL
    ):
        errors.append(
            f"{location}.orphan_tail_max_fill must be "
            f"{CANONICAL_ORPHAN_TAIL_MAX_FILL:.2f}"
        )


def _validate_pptx(value: Any, location: str, errors: list[str]) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location} must be an object")
        return
    unknown = sorted(set(value) - PPTX_FIELDS)
    if unknown:
        errors.append(f"{location} has unknown field(s): {', '.join(unknown)}")
    missing = sorted(PPTX_FIELDS - set(value))
    if missing:
        errors.append(f"{location} is missing field(s): {', '.join(missing)}")
    if "target_slides" in value:
        _validate_range(value["target_slides"], f"{location}.target_slides", errors)
    if "hard_max_slides" in value and not _nonnegative_integer(
        value["hard_max_slides"]
    ):
        errors.append(f"{location}.hard_max_slides must be a nonnegative integer")


def _validate_limits(
    value: Any,
    location: str,
    errors: list[str],
    *,
    section: bool,
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location} must be an object")
        return
    allowed = set(SECTION_LIMIT_FIELDS)
    if section:
        allowed.update({"role", "requires_analysis"})
    unknown = sorted(set(value) - allowed)
    if unknown:
        errors.append(f"{location} has unknown field(s): {', '.join(unknown)}")
    for field in SECTION_LIMIT_FIELDS & set(value):
        if not _nonnegative_integer(value[field]):
            errors.append(f"{location}.{field} must be a nonnegative integer")
    if section:
        if value.get("role") not in SECTION_ROLES:
            errors.append(
                f"{location}.role must be one of: "
                + ", ".join(sorted(SECTION_ROLES))
            )
        if not isinstance(value.get("requires_analysis"), bool):
            errors.append(f"{location}.requires_analysis must be a boolean")


def _validate_content(
    value: Any,
    location: str,
    errors: list[str],
    *,
    allow_empty_sections: bool,
) -> None:
    if not isinstance(value, dict):
        errors.append(f"{location} must be an object")
        return
    unknown = sorted(set(value) - {"defaults", "sections"})
    if unknown:
        errors.append(f"{location} has unknown field(s): {', '.join(unknown)}")
    if set(value) != {"defaults", "sections"}:
        errors.append(f"{location} must contain exactly defaults and sections")
    _validate_limits(value.get("defaults"), f"{location}.defaults", errors, section=False)
    sections = value.get("sections")
    if not isinstance(sections, dict):
        errors.append(f"{location}.sections must be an object")
        return
    if not sections and not allow_empty_sections:
        errors.append(f"{location}.sections must be non-empty")
    for key, limits in sections.items():
        if not isinstance(key, str) or not key.strip():
            errors.append(f"{location}.sections keys must be non-empty strings")
        _validate_limits(
            limits,
            f"{location}.sections.{key}",
            errors,
            section=True,
        )


def _validate_forced_breaks(
    value: Any,
    location: str,
    errors: list[str],
) -> None:
    if not isinstance(value, list):
        errors.append(f"{location} must be a list")
        return
    if any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append(f"{location} entries must be non-empty strings")
    if len(value) != len(set(value)):
        errors.append(f"{location} entries must be unique")


def _validate_selector(
    value: Any,
    modes: Any,
    errors: list[str],
) -> None:
    if not isinstance(value, dict):
        errors.append("layout budget selector must be an object")
        return
    unknown = sorted(set(value) - {"path", "default"})
    if unknown:
        errors.append(
            "layout budget selector has unknown field(s): " + ", ".join(unknown)
        )
    if set(value) != {"path", "default"}:
        errors.append("layout budget selector must contain exactly path and default")
        return
    if value["path"] not in SELECTOR_PATHS:
        errors.append(
            "layout budget selector.path must be one of: "
            + ", ".join(sorted(SELECTOR_PATHS))
        )
    default = value["default"]
    if not isinstance(default, str) or not default:
        errors.append("layout budget selector.default must be a non-empty string")
    elif isinstance(modes, dict) and default not in modes:
        errors.append(
            f"layout budget selector.default {default!r} is not a declared mode"
        )


def _section_identifiers(section: dict[str, Any], index: int) -> set[str]:
    identifiers = {
        str(section.get("num", index)).strip(),
        str(section.get("id", "")).strip(),
    } - {""}
    resolved = identifiers | {
        value.lstrip("0") or "0"
        for value in identifiers
        if value.isdigit()
    }
    appendix = re.match(
        r"^Appendix(?:\s+([A-Z]))?\b",
        str(section.get("title", "")),
        re.IGNORECASE,
    )
    if appendix is not None:
        resolved.add((appendix.group(1) or "A").upper())
    return resolved


def _report_sections(report: dict[str, Any]) -> list[Any]:
    sections = report.get("sections")
    if sections is None:
        sections = report.get("slides", [])
    return sections if isinstance(sections, list) else []


def _validate_resolution(
    budget: dict[str, Any],
    report: dict[str, Any],
    errors: list[str],
) -> None:
    sections = budget.get("content", {}).get("sections", {})
    if not isinstance(sections, dict):
        return
    resolved: dict[str, list[dict[str, Any]]] = {}
    for index, section in enumerate(_report_sections(report), start=1):
        if not isinstance(section, dict):
            continue
        for identifier in _section_identifiers(section, index):
            resolved.setdefault(identifier, []).append(section)
    for configured in sections:
        normalized = configured.lstrip("0") or "0"
        matches = resolved.get(normalized, [])
        if len(matches) != 1:
            errors.append(
                f"configured section {configured!r} resolves {len(matches)} "
                "times; expected exactly once"
            )
    for configured in budget.get("forced_breaks", []):
        if not isinstance(configured, str):
            continue
        normalized = configured.lstrip("0") or "0"
        matches = resolved.get(normalized, [])
        if len(matches) != 1:
            errors.append(
                f"forced break {configured!r} resolves {len(matches)} "
                "times; expected exactly once"
            )


def _validate_effective(
    budget: dict[str, Any],
    report: dict[str, Any] | None,
) -> list[str]:
    errors: list[str] = []
    unknown = sorted(set(budget) - (ROOT_FIELDS - {"selector", "modes"}))
    if unknown:
        errors.append("layout budget has unknown field(s): " + ", ".join(unknown))
    required = {"schema_version", "design_profile", "forced_breaks", "pdf", "content"}
    missing = sorted(required - set(budget))
    if missing:
        errors.append("layout budget is missing field(s): " + ", ".join(missing))
    if budget.get("schema_version") != SCHEMA_VERSION:
        errors.append(
            f"layout budget schema_version must be exactly {SCHEMA_VERSION}"
        )
    if budget.get("design_profile") not in DESIGN_PROFILES:
        errors.append(
            "layout budget design_profile must be one of: "
            + ", ".join(sorted(DESIGN_PROFILES))
        )
    _validate_forced_breaks(
        budget.get("forced_breaks"),
        "layout budget forced_breaks",
        errors,
    )
    _validate_pdf(budget.get("pdf"), "layout budget pdf", errors)
    if "pptx" in budget:
        _validate_pptx(budget["pptx"], "layout budget pptx", errors)
    _validate_content(
        budget.get("content"),
        "layout budget content",
        errors,
        allow_empty_sections=False,
    )
    if report is not None and not errors:
        _validate_resolution(budget, report, errors)
    return errors


def validate_layout_budget(
    budget: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> list[str]:
    """Return strict canonical schema-v2 and section-resolution errors."""
    if not isinstance(budget, dict):
        return ["layout budget root must be an object"]
    if "modes" not in budget:
        if "selector" in budget:
            return ["layout budget selector requires modes"]
        return _validate_effective(budget, report)

    errors: list[str] = []
    unknown = sorted(set(budget) - ROOT_FIELDS)
    if unknown:
        errors.append("layout budget has unknown field(s): " + ", ".join(unknown))
    modes = budget.get("modes")
    if not isinstance(modes, dict) or not modes:
        errors.append("layout budget modes must be a non-empty object")
        return errors
    _validate_selector(budget.get("selector"), modes, errors)
    try:
        selected_mode = _selected_mode(budget, report or {})
    except LayoutBudgetSchemaError:
        selected_mode = None
    base = {
        key: copy.deepcopy(value)
        for key, value in budget.items()
        if key not in {"selector", "modes"}
    }
    base_errors = _validate_effective(base, None)
    errors.extend(
        error
        for error in base_errors
        if error != "layout budget content.sections must be non-empty"
    )
    for name, override in modes.items():
        if not isinstance(name, str) or not name:
            errors.append("layout budget mode names must be non-empty strings")
            continue
        if not isinstance(override, dict):
            errors.append(f"layout budget modes.{name} must be an object")
            continue
        unknown_mode = sorted(set(override) - MODE_FIELDS)
        if unknown_mode:
            errors.append(
                f"layout budget modes.{name} has unknown field(s): "
                + ", ".join(unknown_mode)
            )
            continue
        _validate_mode_override(
            override,
            f"layout budget modes.{name}",
            errors,
        )
        try:
            effective = _merge_mode(base, override)
        except LayoutBudgetSchemaError as error:
            errors.extend(f"modes.{name}: {item}" for item in error.errors)
            continue
        mode_errors = _validate_effective(
            effective,
            report if selected_mode == name else None,
        )
        errors.extend(f"modes.{name}: {error}" for error in mode_errors)
    return errors


def _selected_mode(budget: dict[str, Any], report: dict[str, Any]) -> str:
    selector = budget.get("selector")
    if not isinstance(selector, dict):
        raise LayoutBudgetSchemaError(
            ["layout budget with modes requires a declared selector"]
        )
    path = selector.get("path")
    default = selector.get("default")
    if not isinstance(path, str) or path not in SELECTOR_PATHS:
        raise LayoutBudgetSchemaError(["layout budget selector.path is invalid"])
    value: Any = report
    for part in path.split("."):
        value = value.get(part) if isinstance(value, dict) else None
    selected = value if isinstance(value, str) and value else default
    if not isinstance(selected, str) or not selected:
        raise LayoutBudgetSchemaError(
            [f"layout budget selector {path!r} did not resolve a mode"]
        )
    return selected


def _merge_mode(
    base: dict[str, Any],
    override: dict[str, Any],
) -> dict[str, Any]:
    effective = copy.deepcopy(base)
    for field in ("forced_breaks", "pdf", "pptx"):
        if field in override:
            effective[field] = copy.deepcopy(override[field])
    if "content" in override:
        content = override["content"]
        if not isinstance(content, dict):
            raise LayoutBudgetSchemaError(["mode content must be an object"])
        merged = copy.deepcopy(effective.get("content", {}))
        defaults = content.get("defaults")
        sections = content.get("sections")
        if defaults is not None:
            if not isinstance(defaults, dict):
                raise LayoutBudgetSchemaError(
                    ["mode content.defaults must be an object"]
                )
            merged.setdefault("defaults", {}).update(copy.deepcopy(defaults))
        if sections is not None:
            if not isinstance(sections, dict):
                raise LayoutBudgetSchemaError(
                    ["mode content.sections must be an object"]
                )
            merged.setdefault("sections", {}).update(copy.deepcopy(sections))
        effective["content"] = merged
    return effective


def _validate_mode_override(
    value: dict[str, Any],
    location: str,
    errors: list[str],
) -> None:
    """Validate fields declared directly by one mode before inheritance."""
    if "forced_breaks" in value:
        _validate_forced_breaks(
            value["forced_breaks"],
            f"{location}.forced_breaks",
            errors,
        )
    if "pdf" in value:
        _validate_pdf(value["pdf"], f"{location}.pdf", errors)
    if "pptx" in value:
        _validate_pptx(value["pptx"], f"{location}.pptx", errors)
    content = value.get("content")
    if content is None:
        return
    if not isinstance(content, dict):
        errors.append(f"{location}.content must be an object")
        return
    unknown = sorted(set(content) - {"defaults", "sections"})
    if unknown:
        errors.append(
            f"{location}.content has unknown field(s): {', '.join(unknown)}"
        )
    if "defaults" in content:
        _validate_limits(
            content["defaults"],
            f"{location}.content.defaults",
            errors,
            section=False,
        )
    sections = content.get("sections")
    if sections is not None:
        if not isinstance(sections, dict):
            errors.append(f"{location}.content.sections must be an object")
        else:
            for key, limits in sections.items():
                if not isinstance(key, str) or not key.strip():
                    errors.append(
                        f"{location}.content.sections keys must be non-empty strings"
                    )
                _validate_limits(
                    limits,
                    f"{location}.content.sections.{key}",
                    errors,
                    section=True,
                )


def resolve_layout_budget(
    budget: dict[str, Any],
    report: dict[str, Any],
) -> dict[str, Any]:
    """Resolve a declared selector and return one strict effective budget."""
    if "modes" not in budget:
        return copy.deepcopy(budget)
    mode = _selected_mode(budget, report)
    modes = budget.get("modes")
    selected = modes.get(mode) if isinstance(modes, dict) else None
    if not isinstance(selected, dict):
        available = ", ".join(sorted(modes)) if isinstance(modes, dict) else ""
        raise LayoutBudgetSchemaError(
            [f"layout budget has no mode {mode!r}; available: {available}"]
        )
    base = {
        key: copy.deepcopy(value)
        for key, value in budget.items()
        if key not in {"selector", "modes"}
    }
    effective = _merge_mode(base, selected)
    errors = _validate_effective(effective, None)
    if errors:
        raise LayoutBudgetSchemaError(errors)
    return effective


def load_layout_budget(path: Path) -> dict[str, Any]:
    """Load a layout budget with stable parse diagnostics."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise LayoutBudgetSchemaError(
            [f"unable to read layout budget {path}: {error}"]
        ) from error
    except json.JSONDecodeError as error:
        raise LayoutBudgetSchemaError(
            [
                f"invalid layout budget JSON at line {error.lineno}, "
                f"column {error.colno}: {error.msg}"
            ]
        ) from error
    if not isinstance(value, dict):
        raise LayoutBudgetSchemaError(["layout budget root must be an object"])
    return value
