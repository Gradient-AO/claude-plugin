#!/usr/bin/env python3
"""Generate uncommitted release-review artifacts from the fictional golden source."""

from __future__ import annotations

import argparse
import os
import pathlib
import subprocess
import sys

if str(pathlib.Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import PLUGIN_ROOT, normalize_pptx

ROOT = PLUGIN_ROOT
SOURCE = ROOT / "tests" / "fixtures" / "golden-report.json"
RENDERER = ROOT / "shared" / "render.py"
_normalize_pptx = normalize_pptx


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
        normalize_pptx(pptx_path, nested_xlsx=True)
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
