#!/usr/bin/env python3
"""Generate one illustrative PDF and editable PowerPoint example per skill."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (
    EXAMPLE_DIRECT_SOURCES as DIRECT_SOURCES,
    EXAMPLE_GIPS_SOURCES as GIPS_SOURCES,
    FIXED_TIME,
    PLUGIN_ROOT,
    ZIP_TIME,
    normalize_pptx,
)

ROOT = PLUGIN_ROOT
FIXTURES = ROOT / "tests" / "fixtures"
QA_RENDERER = ROOT / "shared" / "qa_report.py"
GIPS_COMPOSER = (
    ROOT / "internal" / "gips-evidence-review" / "scripts" / "compose_gips_report.py"
)


def skill_for_artifact(artifact: str) -> str:
    """Resolve a mode-specific example filename to its installed skill."""
    if artifact.startswith("gradient-allocation-study-"):
        return "gradient-allocation-study"
    if artifact.startswith("gradient-manager-evaluation-"):
        return "gradient-manager-evaluation"
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
        "gradient-manager-evaluation-fit": (
            "gradient-manager-evaluation",
            "references/fit-layout-budget.json",
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
