#!/usr/bin/env python3
"""Generate one fictional PDF and editable PowerPoint example per skill."""

from __future__ import annotations

import argparse
import datetime
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
RENDERER = ROOT / "shared" / "render.py"
GIPS_COMPOSER = (
    ROOT / "skills" / "gradient-gips-standards" / "scripts" / "compose_gips_report.py"
)
FIXED_TIME = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
ZIP_TIME = (2020, 1, 1, 0, 0, 0)

DIRECT_SOURCES = {
    "gradient-ddq-reconcile": "ddq.json",
    "gradient-equity-note": "equity.json",
    "gradient-fixed-income-portfolio-construction": "construction-fixed-income.json",
    "gradient-global-public-equity-portfolio-construction": "construction-global-public-equity.json",
    "gradient-ic-memo": "ic-memo.json",
    "gradient-macro-brief": "deck.json",
    "gradient-manager-compare": "compare.json",
    "gradient-manager-monitor": "digest.json",
    "gradient-marketable-alternatives-portfolio-construction": "portfolio-construction-marketable-alternatives.json",
    "gradient-odd-report": "odd.json",
    "gradient-portfolio-attribution-report": "portfolio-attribution-report.json",
    "gradient-portfolio-review": "portfolio-comprehensive.json",
    "gradient-private-markets-portfolio-construction": "construction-private-markets.json",
    "gradient-real-assets-portfolio-construction": "portfolio-construction-real-assets.json",
    "gradient-setup": "setup.json",
}

GIPS_SOURCES = {
    "gradient-gips-manager-diligence": ("gips.md", "gips_visuals.json", "gips_meta.json"),
    "gradient-gips-asset-owner-review": (
        "gips" "-asset-owner-review.md",
        "gips" "-asset-owner-review-visuals.json",
        "gips" "-asset-owner-review-meta.json",
    ),
    "gradient-gips-policies-gap-check": (
        "gips" "-policies-gap-check.md",
        "gips" "-policies-gap-check-visuals.json",
        "gips" "-policies-gap-check-meta.json",
    ),
    "gradient-gips-report-review": (
        "gips" "-report-review.md",
        "gips" "-report-review-visuals.json",
        "gips" "-report-review-meta.json",
    ),
}


def normalize_pptx(path: Path) -> None:
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
        temporary = Path(handle.name)
    try:
        with zipfile.ZipFile(path, "r") as source, zipfile.ZipFile(
            temporary, "w"
        ) as target:
            for source_info in source.infolist():
                info = zipfile.ZipInfo(source_info.filename, ZIP_TIME)
                info.compress_type = source_info.compress_type
                info.external_attr = source_info.external_attr
                info.create_system = source_info.create_system
                target.writestr(info, source.read(source_info.filename))
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def gips_source(skill: str, directory: Path) -> Path:
    """Compose one GIPS fixture through the production handoff."""
    markdown, visuals, meta = GIPS_SOURCES[skill]
    output = directory / f"{skill}.json"
    subprocess.run(
        [
            sys.executable,
            str(GIPS_COMPOSER),
            str(FIXTURES / markdown),
            str(FIXTURES / visuals),
            str(FIXTURES / meta),
            str(output),
        ],
        check=True,
    )
    return output


def gips_reference_source(directory: Path) -> Path:
    """Convert the GIPS reference note to canonical report JSON."""
    renderer_path = ROOT / "shared" / "gradient_report.py"
    spec = importlib.util.spec_from_file_location("gradient_report_example", renderer_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load shared report converter")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    markdown = (FIXTURES / "note.md").read_text(encoding="utf-8")
    meta: dict[str, Any] = json.loads(
        (FIXTURES / "note_meta.json").read_text(encoding="utf-8")
    )
    output = directory / "gradient-gips-standards.json"
    output.write_text(
        json.dumps(module.md_document_to_report(markdown, meta), indent=2),
        encoding="utf-8",
    )
    return output


def main() -> int:
    """Generate the public fictional reference set."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "assets" / "examples",
    )
    parser.add_argument(
        "--format",
        choices=("pdf", "pptx", "both"),
        default="both",
        dest="output_format",
    )
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ)
    environment.setdefault("SOURCE_DATE_EPOCH", "1577836800")
    with tempfile.TemporaryDirectory() as temporary_name:
        temporary = Path(temporary_name)
        sources = {
            skill: FIXTURES / filename
            for skill, filename in DIRECT_SOURCES.items()
        }
        sources.update(
            {skill: gips_source(skill, temporary) for skill in GIPS_SOURCES}
        )
        sources["gradient-gips-standards"] = gips_reference_source(temporary)
        for skill in sorted(sources):
            base = args.out / skill
            completed = subprocess.run(
                [
                    sys.executable,
                    str(RENDERER),
                    str(sources[skill]),
                    "--format",
                    args.output_format,
                    "--out",
                    str(base),
                ],
                env=environment,
                check=False,
            )
            if completed.returncode != 0:
                return completed.returncode
            pptx_path = base.with_suffix(".pptx")
            if pptx_path.is_file():
                normalize_pptx(pptx_path)
    print(f"Generated 20 fictional examples in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
