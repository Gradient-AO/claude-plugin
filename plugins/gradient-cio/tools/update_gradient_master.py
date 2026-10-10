#!/usr/bin/env python3
"""Deterministically align gradient-master.potx with the canonical report theme."""

from __future__ import annotations

import sys
import tempfile
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "shared"))

from report_theme import (  # noqa: E402
    AMBER,
    COLORS,
    CORAL,
    FONT_FAMILY,
    INK,
    LIME,
    LIME_DK,
    PANEL,
    PAPER,
    PPTX_SLIDE_HEIGHT_IN,
    PPTX_SLIDE_WIDTH_IN,
    WASH,
    pptx_hex,
    validate_potx_theme,
)


NAMESPACE = "http://schemas.openxmlformats.org/drawingml/2006/main"
ET.register_namespace("a", NAMESPACE)


def update_theme_xml(payload: bytes) -> bytes:
    """Return a theme XML payload using canonical fonts and core colors."""
    root = ET.fromstring(payload)
    ns = {"a": NAMESPACE}
    for node in root.findall(".//a:fontScheme//a:latin", ns):
        node.set("typeface", FONT_FAMILY)
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
    scheme = root.find(".//a:themeElements/a:clrScheme", ns)
    if scheme is None:
        raise RuntimeError("PowerPoint template has no color scheme")
    for child in list(scheme):
        name = child.tag.rsplit("}", 1)[-1]
        if name not in expected:
            continue
        color = next(iter(child), None)
        if color is None:
            color = ET.SubElement(child, f"{{{NAMESPACE}}}srgbClr")
        color.tag = f"{{{NAMESPACE}}}srgbClr"
        color.attrib.clear()
        color.set("val", expected[name])
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def update_presentation_xml(payload: bytes) -> bytes:
    """Return presentation XML using canonical 16:9 slide dimensions."""
    root = ET.fromstring(payload)
    presentation_namespace = (
        "http://schemas.openxmlformats.org/presentationml/2006/main"
    )
    slide_size = root.find(f"{{{presentation_namespace}}}sldSz")
    if slide_size is None:
        raise RuntimeError("PowerPoint template has no slide size")
    slide_size.set("cx", str(round(PPTX_SLIDE_WIDTH_IN * 914400)))
    slide_size.set("cy", str(round(PPTX_SLIDE_HEIGHT_IN * 914400)))
    slide_size.set("type", "screen16x9")
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)


def update_template(path: Path) -> None:
    """Rewrite only the theme part while preserving deterministic ZIP metadata."""
    with tempfile.NamedTemporaryFile(
        dir=path.parent, suffix=".potx", delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
            temporary, "w"
        ) as target:
            for source_info in source.infolist():
                payload = source.read(source_info.filename)
                if source_info.filename == "ppt/theme/theme1.xml":
                    payload = update_theme_xml(payload)
                elif source_info.filename == "ppt/presentation.xml":
                    payload = update_presentation_xml(payload)
                info = zipfile.ZipInfo(source_info.filename, source_info.date_time)
                info.compress_type = source_info.compress_type
                info.comment = source_info.comment
                info.extra = source_info.extra
                info.internal_attr = source_info.internal_attr
                info.external_attr = source_info.external_attr
                info.create_system = source_info.create_system
                target.writestr(info, payload)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    path = ROOT / "assets" / "gradient-master.potx"
    update_template(path)
    errors = validate_potx_theme(path)
    if errors:
        for error in errors:
            print(f"FAIL — {error}")
        return 1
    print(f"PASS — updated {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
