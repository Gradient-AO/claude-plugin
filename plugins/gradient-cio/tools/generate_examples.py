#!/usr/bin/env python3
"""Generate one illustrative PDF and editable PowerPoint example per skill."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
QA_RENDERER = ROOT / "shared" / "qa_report.py"
GIPS_COMPOSER = (
    ROOT / "internal" / "gips-evidence-review" / "scripts" / "compose_gips_report.py"
)
FIXED_TIME = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
ZIP_TIME = (2020, 1, 1, 0, 0, 0)

DIRECT_SOURCES = {
    "gradient-odd-ddq-reconcile": "ddq.json",
    "gradient-idd-manager-performance-single": "idd-manager-performance-single.json",
    "gradient-idd-manager-performance-compare": "idd-manager-performance-compare.json",
    "gradient-idd-manager-performance-robustness": "idd-manager-performance-robustness.json",
    "gradient-idd-manager-performance-shortlist": "idd-shortlist.json",
    "gradient-idd-manager-portfolio-fit": "idd-portfolio-fit.json",
    "gradient-idd-private-markets-pme": "idd-private-markets-pme.json",
    "gradient-portfolio-construction-fixed-income": "construction-fixed-income.json",
    "gradient-portfolio-construction-global-public-equity": "construction-global-public-equity.json",
    "gradient-decision-ic-memo": "ic-memo.json",
    "gradient-odd-report-compare": "compare.json",
    "gradient-odd-manager-monitor": "digest.json",
    "gradient-odd-manager-monitor-triage": "triage.json",
    "gradient-portfolio-construction-marketable-alternatives": "construction-marketable-alternatives.json",
    "gradient-odd-report": "odd.json",
    "gradient-portfolio-attribution": "portfolio-attribution-report.json",
    "gradient-portfolio-attribution-lanes-fallback": "attribution-compare-fallback.json",
    "gradient-portfolio-attribution-lanes-three-lane": "attribution-compare-three-lane.json",
    "gradient-portfolio-review": "portfolio-comprehensive.json",
    "gradient-portfolio-construction-private-markets": "construction-private-markets.json",
    "gradient-portfolio-construction-real-assets": "construction-real-assets.json",
    "gradient-setup": "setup.json",
}

GIPS_SOURCES = {
    "internal-gips-review-asset-owner": (
        "gips" "-asset-owner-review.md",
        "gips" "-asset-owner-review-visuals.json",
        "gips" "-asset-owner-review-meta.json",
    ),
    "internal-gips-review-firm": (
        "gips" "-report-review.md",
        "gips" "-report-review-visuals.json",
        "gips" "-report-review-meta.json",
    ),
}


def skill_for_artifact(artifact: str) -> str:
    """Resolve a mode-specific example filename to its installed skill."""
    if artifact.startswith("gradient-portfolio-construction-"):
        return "gradient-portfolio-construction"
    if artifact.startswith("gradient-idd-manager-performance-"):
        return "gradient-idd-manager-performance"
    if artifact.startswith("gradient-odd-report-"):
        return "gradient-odd-report"
    if artifact.startswith("gradient-odd-manager-monitor-"):
        return "gradient-odd-manager-monitor"
    if artifact.startswith("gradient-portfolio-attribution-lanes-"):
        return "gradient-portfolio-attribution"
    return artifact


def budget_for_artifact(artifact: str) -> Path:
    """Resolve public-skill and internal-module layout budgets."""
    if artifact.startswith("internal-gips-review-"):
        return ROOT / "internal" / "gips-evidence-review" / "references" / "layout-budget.json"
    mode_budgets = {
        "gradient-idd-manager-performance-shortlist": (
            "gradient-idd-manager-performance",
            "references/modes/shortlist-layout-budget.json",
        ),
        "gradient-odd-report-compare": (
            "gradient-odd-report",
            "references/layout-budget-compare.json",
        ),
        "gradient-odd-manager-monitor-triage": (
            "gradient-odd-manager-monitor",
            "references/layout-budget-triage.json",
        ),
        "gradient-portfolio-attribution-lanes-fallback": (
            "gradient-portfolio-attribution",
            "references/modes/compare-lanes-layout-budget.json",
        ),
        "gradient-portfolio-attribution-lanes-three-lane": (
            "gradient-portfolio-attribution",
            "references/modes/compare-lanes-layout-budget.json",
        ),
    }
    if artifact in mode_budgets:
        skill, relative_path = mode_budgets[artifact]
        return ROOT / "skills" / skill / relative_path
    return (
        ROOT
        / "skills"
        / skill_for_artifact(artifact)
        / "references"
        / "layout-budget.json"
    )


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


def main() -> int:
    """Generate the public illustrative reference set."""
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
        suffixes = (
            (".pdf", ".pptx")
            if args.output_format == "both"
            else (f".{args.output_format}",)
        )
        failed: list[str] = []
        unrendered: list[str] = []
        for skill in sorted(sources):
            work = temporary / "qa" / skill
            work.mkdir(parents=True)
            completed = subprocess.run(
                [
                    sys.executable,
                    str(QA_RENDERER),
                    str(sources[skill]),
                    "--format",
                    args.output_format,
                    "--out",
                    str(work / skill),
                    "--budget",
                    str(budget_for_artifact(skill)),
                ],
                env=environment,
                check=False,
            )
            if not all(
                (work / skill).with_suffix(suffix).is_file()
                for suffix in suffixes
            ):
                unrendered.append(skill)
            elif completed.returncode != 0:
                failed.append(skill)
            base = args.out / skill
            for suffix in (".pdf", ".pptx"):
                rendered = (work / skill).with_suffix(suffix)
                if rendered.is_file():
                    shutil.move(rendered, base.with_suffix(suffix))
            pptx_path = base.with_suffix(".pptx")
            if pptx_path.is_file():
                normalize_pptx(pptx_path)
    if failed:
        print(
            "Layout QA warnings for: " + ", ".join(failed),
            file=sys.stderr,
        )
    if unrendered:
        print(
            "FAIL — examples rejected before rendering: " + ", ".join(unrendered),
            file=sys.stderr,
        )
        return 1
    print(f"Generated {len(sources)} illustrative examples in {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
