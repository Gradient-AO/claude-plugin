#!/usr/bin/env python3
"""Generate uncommitted release-review artifacts from the fictional golden source."""

from __future__ import annotations

import argparse
import datetime
import io
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import zipfile


ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "tests" / "fixtures" / "golden-report.json"
RENDERER = ROOT / "shared" / "render.py"
FIXED_TIME = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
ZIP_TIME = (2020, 1, 1, 0, 0, 0)
CORE_TIMESTAMP = re.compile(
    rb"(<dcterms:(?:created|modified)[^>]*>)[^<]*(</dcterms:(?:created|modified)>)"
)


def _normalized_zip(payload: bytes) -> bytes:
    source_buffer = io.BytesIO(payload)
    target_buffer = io.BytesIO()
    with zipfile.ZipFile(source_buffer, "r") as source, zipfile.ZipFile(
        target_buffer, "w"
    ) as target:
        for source_info in source.infolist():
            content = source.read(source_info.filename)
            if source_info.filename == "docProps/core.xml":
                content = CORE_TIMESTAMP.sub(
                    rb"\g<1>2020-01-01T00:00:00Z\g<2>", content
                )
            info = zipfile.ZipInfo(source_info.filename, ZIP_TIME)
            info.compress_type = source_info.compress_type
            info.comment = source_info.comment
            info.extra = source_info.extra
            info.internal_attr = source_info.internal_attr
            info.external_attr = source_info.external_attr
            info.create_system = source_info.create_system
            target.writestr(info, content)
    return target_buffer.getvalue()


def _normalize_pptx(path: pathlib.Path) -> None:
    """Remove volatile Office timestamps and normalize ZIP member dates."""
    from pptx import Presentation

    presentation = Presentation(path)
    presentation.core_properties.created = FIXED_TIME
    presentation.core_properties.modified = FIXED_TIME
    presentation.core_properties.last_modified_by = "GradientCIO"
    presentation.save(path)

    with tempfile.NamedTemporaryFile(
        dir=path.parent, suffix=".pptx", delete=False
    ) as handle:
        temporary = pathlib.Path(handle.name)
    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
            temporary, "w"
        ) as target:
            for source_info in source.infolist():
                content = source.read(source_info.filename)
                if source_info.filename.endswith(".xlsx"):
                    content = _normalized_zip(content)
                info = zipfile.ZipInfo(source_info.filename, ZIP_TIME)
                info.compress_type = source_info.compress_type
                info.comment = source_info.comment
                info.extra = source_info.extra
                info.internal_attr = source_info.internal_attr
                info.external_attr = source_info.external_attr
                info.create_system = source_info.create_system
                target.writestr(info, content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=pathlib.Path,
        required=True,
        help="directory for generated review artifacts",
    )
    parser.add_argument(
        "--format",
        choices=("pdf", "pptx", "both"),
        default="both",
        dest="output_format",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    base = args.out / "gradientcio-golden-report-test"
    environment = dict(os.environ)
    environment.setdefault("SOURCE_DATE_EPOCH", "1577836800")
    result = subprocess.run(
        [
            sys.executable,
            str(RENDERER),
            str(SOURCE),
            "--format",
            args.output_format,
            "--out",
            str(base),
        ],
        env=environment,
        check=False,
    )
    if result.returncode != 0:
        return result.returncode
    pptx_path = base.with_suffix(".pptx")
    if pptx_path.is_file():
        _normalize_pptx(pptx_path)
    generated = [
        str(path)
        for path in (base.with_suffix(".pdf"), pptx_path)
        if path.is_file()
    ]
    print("Generated fictional release-review artifacts:")
    for path in generated:
        print(f"  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
