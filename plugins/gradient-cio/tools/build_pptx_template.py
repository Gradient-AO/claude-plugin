#!/usr/bin/env python3
"""Build the deterministic, zero-slide Gradient PowerPoint master."""

from __future__ import annotations

import datetime
import os
import re
import tempfile
import zipfile
from pathlib import Path

from pptx import Presentation


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "gradient-master.potx"
ZIP_TIME = (2020, 1, 1, 0, 0, 0)
LAYOUT_NAMES = (
    "Cover",
    "Section divider",
    "Exhibit",
    "Two-up",
    "Table",
    "Text",
    "Appendix",
)


def main() -> int:
    """Create a theme-font template consumed by the shared renderer."""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    presentation = Presentation()
    fixed = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    presentation.core_properties.title = "Gradient PowerPoint Master"
    presentation.core_properties.author = "GradientCIO"
    presentation.core_properties.created = fixed
    presentation.core_properties.modified = fixed
    presentation.core_properties.last_modified_by = "GradientCIO"
    for layout in list(presentation.slide_layouts)[len(LAYOUT_NAMES) :]:
        presentation.slide_layouts.remove(layout)
    for layout, name in zip(presentation.slide_layouts, LAYOUT_NAMES):
        layout.name = name

    with tempfile.NamedTemporaryFile(
        dir=OUTPUT.parent, suffix=".pptx", delete=False
    ) as handle:
        source_path = Path(handle.name)
    with tempfile.NamedTemporaryFile(
        dir=OUTPUT.parent, suffix=".potx", delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        presentation.save(source_path)
        with zipfile.ZipFile(source_path, "r") as source, zipfile.ZipFile(
            temporary, "w"
        ) as target:
            for source_info in source.infolist():
                payload = source.read(source_info.filename)
                if source_info.filename == "ppt/theme/theme1.xml":
                    text = payload.decode("utf-8")
                    text = re.sub(
                        r'<a:latin typeface="[^"]*"/>',
                        '<a:latin typeface="Inter"/>',
                        text,
                    )
                    payload = text.encode("utf-8")
                elif source_info.filename == "[Content_Types].xml":
                    payload = payload.replace(
                        b"application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml",
                        b"application/vnd.openxmlformats-officedocument.presentationml.template.main+xml",
                    )
                info = zipfile.ZipInfo(source_info.filename, ZIP_TIME)
                info.compress_type = source_info.compress_type
                info.external_attr = source_info.external_attr
                info.create_system = source_info.create_system
                target.writestr(info, payload)
        os.replace(temporary, OUTPUT)
    finally:
        source_path.unlink(missing_ok=True)
        temporary.unlink(missing_ok=True)
    print(f"Wrote {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
