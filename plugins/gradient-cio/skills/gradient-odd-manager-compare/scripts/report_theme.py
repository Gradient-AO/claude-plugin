#!/usr/bin/env python3
"""Canonical Gradient report visual-system tokens and branding contracts."""

from __future__ import annotations

import json
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


THEME_VERSION = "2.2.0"
FONT_FAMILY = "Inter"
FONT_FALLBACK = ("Arial", "sans-serif")

COLORS = {
    "ink": "#0D1117",
    "panel": "#161C24",
    "accent": "#C6F432",
    "accent_dark": "#4F6B00",
    "ink_secondary": "#4A5563",
    "muted": "#8A94A1",
    "rule": "#E3E7EC",
    "paper": "#FFFFFF",
    "wash": "#F5F7F9",
    "positive": "#C6F432",
    "warning": "#F2A93B",
    "adverse": "#FF6B5E",
    "neutral": "#9AA5B1",
    "blue": "#5B8DEF",
    "teal": "#3FB8AF",
    "purple": "#B58AE0",
    "text_on_dark": "#F2F5F7",
    "text_on_dark_muted": "#A7B1BC",
    "powered_by_muted": "#6E7A87",
    "dark_rule": "#242C36",
    "dark_meter": "#2B3440",
}

INK = COLORS["ink"]
PANEL = COLORS["panel"]
LIME = COLORS["accent"]
LIME_DK = COLORS["accent_dark"]
INK2 = COLORS["ink_secondary"]
MUTED = COLORS["muted"]
RULE = COLORS["rule"]
PAPER = COLORS["paper"]
WASH = COLORS["wash"]
AMBER = COLORS["warning"]
CORAL = COLORS["adverse"]
SLATE = COLORS["neutral"]
TEXT_ON_DARK = COLORS["text_on_dark"]
TEXT_ON_DARK_MUTED = COLORS["text_on_dark_muted"]
POWERED_BY_MUTED = COLORS["powered_by_muted"]
DARK_RULE = COLORS["dark_rule"]
DARK_METER = COLORS["dark_meter"]

SERIES = (
    INK,
    "#7FA600",
    AMBER,
    COLORS["blue"],
    CORAL,
    SLATE,
)
PIE = SERIES[:5] + (COLORS["teal"], COLORS["purple"], SLATE)

PDF_PAGE_MARGINS_IN = {
    "top": 0.72,
    "right": 0.75,
    "bottom": 0.70,
    "left": 0.75,
}
PDF_COVER_PADDING_IN = {
    "top": 0.80,
    "right": 0.75,
    "bottom": 0.80,
    "left": 0.75,
}
PPTX_SLIDE_WIDTH_IN = 13.333
PPTX_SLIDE_HEIGHT_IN = 7.5
PPTX_SAFE_AREA_IN = {
    "left": 0.70,
    "right": 0.70,
    "top": 0.36,
    "bottom": 0.24,
}

TYPE_SCALE_PT = {
    "cover_title_pdf": 34,
    "cover_title_pptx": 34,
    "section_title_pdf": 16,
    "section_title_pptx": 23,
    "body_pdf": 9.4,
    "body_pptx": 11,
    "footer": 7,
}

COVER_FIELD_LIMITS = {
    "title": 110,
    "subtitle": 180,
    "eyebrow": 48,
    "header_label": 48,
    "running_head": 72,
    "data_scope_banner": 120,
    "cover_fact_label": 36,
    "cover_fact_value": 80,
    "cover_facts": 6,
}

BRAND_NAME = "GradientCIO.com"
BRANDING_ALLOWED_FIELDS = frozenset(
    {"brand", "client_name", "client_logo", "confidentiality", "powered_by"}
)
BRANDING_FORBIDDEN_FIELDS = frozenset(
    {
        "color",
        "colors",
        "font",
        "fonts",
        "margin",
        "margins",
        "css",
        "theme",
    }
)

SIGNAL = {
    "clear": ("No flags identified", LIME, INK),
    "consistent": ("Consistent with filings", LIME, INK),
    "compliant": ("Compliant", LIME, INK),
    "satisfactory": ("Satisfactory", LIME, INK),
    "watch": ("Watch", AMBER, INK),
    "review": ("Needs review", AMBER, INK),
    "follow_ups": ("Satisfactory with follow-ups", AMBER, INK),
    "elevated": ("Elevated", CORAL, INK),
    "discrepancies": ("Discrepancies found", CORAL, INK),
    "breach": ("Breach", CORAL, INK),
    "material_concern": ("Material concern", CORAL, INK),
    "insufficient": ("Insufficient evidence", SLATE, INK),
    "not_applicable": ("Not applicable", SLATE, INK),
    "not_assessed": ("Not assessed", SLATE, INK),
    "ready": ("Ready", LIME, INK),
    "partial": ("Partly ready", AMBER, INK),
    "not_ready": ("Not ready", CORAL, INK),
}

STATUS_COLOR = {
    "available": LIME,
    "used": LIME,
    "passed": LIME,
    "aligned": LIME,
    "degraded": AMBER,
    "advisory": AMBER,
    "partial": AMBER,
    "watch": AMBER,
    "warning": AMBER,
    "corroborated": LIME,
    "consistent": LIME,
    "needs_review": AMBER,
    "needs review": AMBER,
    "timing": AMBER,
    "contradicted": CORAL,
    "unverifiable": SLATE,
    "not_checkable": SLATE,
    "analyst": SLATE,
    "unavailable": CORAL,
    "failed": CORAL,
    "missing": CORAL,
    "elevated": CORAL,
    "not_applicable": SLATE,
    "not_run": SLATE,
    "not_assessed": SLATE,
    "compliant": LIME,
    "met": LIME,
    "satisfactory": LIME,
    "complete": LIME,
    "yes": LIME,
    "pass": LIME,
    "approve": LIME,
    "breach": CORAL,
    "bad": CORAL,
    "not met": CORAL,
    "material concern": CORAL,
    "fail": CORAL,
    "partially met": AMBER,
    "satisfactory with follow-ups": AMBER,
    "open": AMBER,
    "not found": SLATE,
    "n/a": SLATE,
    "not assessed": SLATE,
    "closed": SLATE,
    "high": CORAL,
    "medium": AMBER,
    "low": SLATE,
    "new": AMBER,
    "changed": AMBER,
    "resolved": LIME,
    "no change": SLATE,
    "unchanged": SLATE,
    "ready": LIME,
    "connected": LIME,
    "entitled": LIME,
    "ok": LIME,
    "not ready": CORAL,
    "not connected": CORAL,
    "error": CORAL,
    "not entitled": SLATE,
    "not licensed": SLATE,
    "stale": AMBER,
    "conditional": AMBER,
}
SEVERITY_COLOR = {
    "high": CORAL,
    "medium": AMBER,
    "low": SLATE,
    "info": LIME,
}


def css_hex(value: str) -> str:
    """Return one validated CSS ``#RRGGBB`` color."""
    normalized = value.strip().upper().lstrip("#")
    if len(normalized) != 6 or any(character not in "0123456789ABCDEF" for character in normalized):
        raise ValueError(f"invalid theme color: {value!r}")
    return f"#{normalized}"


def pptx_hex(value: str) -> str:
    """Return one validated PowerPoint ``RRGGBB`` color."""
    return css_hex(value).lstrip("#")


def default_confidentiality(branding: dict[str, Any] | None = None) -> str:
    """Return the canonical confidentiality label for a normalized brand."""
    brand = branding or {}
    explicit = str(brand.get("confidentiality") or "").strip()
    if explicit:
        return explicit
    client_name = str(brand.get("client_name") or "").strip()
    if client_name:
        return f"Confidential — prepared for {client_name}"
    return "Confidential — prepared for internal investment use"


def normalize_branding(
    value: dict[str, Any] | None,
    *,
    base_directory: Path | None = None,
) -> dict[str, Any]:
    """Validate branding without permitting theme overrides."""
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError("branding root must be an object")
    forbidden = sorted(
        key
        for key in value
        if key in BRANDING_FORBIDDEN_FIELDS or key not in BRANDING_ALLOWED_FIELDS
    )
    if forbidden:
        raise ValueError(
            "branding contains unsupported field(s): " + ", ".join(forbidden)
        )
    normalized: dict[str, Any] = {}
    brand_kind = value.get("brand")
    if brand_kind is not None:
        if brand_kind not in {"gradient", "client"}:
            raise ValueError("branding.brand must be 'gradient' or 'client'")
        normalized["brand"] = brand_kind
    for key in ("client_name", "confidentiality"):
        if key in value:
            if not isinstance(value[key], str):
                raise ValueError(f"branding.{key} must be a string")
            normalized[key] = value[key].strip()
    if "powered_by" in value:
        if not isinstance(value["powered_by"], bool):
            raise ValueError("branding.powered_by must be a boolean")
        normalized["powered_by"] = value["powered_by"]
    else:
        normalized["powered_by"] = True
    logo = value.get("client_logo")
    if logo is not None and logo != "":
        if not isinstance(logo, str) or not logo.strip():
            raise ValueError("branding.client_logo must be a path string")
        logo_path = Path(logo)
        if not logo_path.is_absolute() and base_directory is not None:
            logo_path = base_directory / logo_path
        logo_path = logo_path.resolve()
        if not logo_path.is_file():
            raise ValueError(f"branding client_logo not found: {logo_path}")
        if logo_path.suffix.casefold() not in {".png", ".jpg", ".jpeg", ".svg"}:
            raise ValueError("branding.client_logo must be PNG, JPEG, or SVG")
        normalized["client_logo"] = str(logo_path)
    return normalized


def load_branding(path: Path | None) -> dict[str, Any]:
    """Load and normalize an explicit branding file."""
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        raise ValueError(f"unable to read branding file {path}: {error}") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"invalid branding JSON at line {error.lineno}, column {error.colno}: {error.msg}"
        ) from error
    return normalize_branding(value, base_directory=path.resolve().parent)


def validate_potx_theme(path: Path) -> list[str]:
    """Return deterministic template deviations from the canonical theme."""
    errors: list[str] = []
    if not path.is_file():
        return [f"PowerPoint template not found: {path}"]
    try:
        with zipfile.ZipFile(path) as archive:
            root = ET.fromstring(archive.read("ppt/theme/theme1.xml"))
            presentation = ET.fromstring(
                archive.read("ppt/presentation.xml")
            )
    except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError) as error:
        return [f"unable to inspect PowerPoint template: {error}"]
    namespace = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
    presentation_namespace = {
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main"
    }
    slide_size = presentation.find("p:sldSz", presentation_namespace)
    expected_width = round(PPTX_SLIDE_WIDTH_IN * 914400)
    expected_height = round(PPTX_SLIDE_HEIGHT_IN * 914400)
    if (
        slide_size is None
        or int(slide_size.attrib.get("cx", 0)) != expected_width
        or int(slide_size.attrib.get("cy", 0)) != expected_height
    ):
        errors.append(
            "PowerPoint template slide size does not match "
            f"{PPTX_SLIDE_WIDTH_IN}×{PPTX_SLIDE_HEIGHT_IN} inches"
        )
    typefaces = {
        node.attrib.get("typeface", "")
        for node in root.findall(".//a:themeElements/a:fontScheme//a:latin", namespace)
    }
    if typefaces != {FONT_FAMILY}:
        errors.append(
            f"PowerPoint template latin fonts {sorted(typefaces)!r} do not match {FONT_FAMILY!r}"
        )
    expected = {
        "dk1": pptx_hex(INK),
        "lt1": pptx_hex(PAPER),
        "dk2": pptx_hex(PANEL),
        "lt2": pptx_hex(WASH),
        "accent1": pptx_hex(LIME),
        "accent2": pptx_hex(LIME_DK),
        "accent3": pptx_hex(AMBER),
        "accent4": pptx_hex(COLORS["blue"]),
        "accent5": pptx_hex(CORAL),
        "accent6": pptx_hex(COLORS["teal"]),
    }
    scheme = root.find(".//a:themeElements/a:clrScheme", namespace)
    if scheme is None:
        errors.append("PowerPoint template has no color scheme")
        return errors
    actual: dict[str, str] = {}
    for child in list(scheme):
        name = child.tag.rsplit("}", 1)[-1]
        color = next(iter(child), None)
        if color is None:
            continue
        actual[name] = color.attrib.get("lastClr") or color.attrib.get("val", "")
    for name, expected_color in expected.items():
        if actual.get(name, "").upper() != expected_color:
            errors.append(
                f"PowerPoint template {name} is {actual.get(name, 'missing')}; expected {expected_color}"
            )
    return errors
