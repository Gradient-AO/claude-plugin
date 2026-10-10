#!/usr/bin/env python3
"""Rasterize committed PDF and PowerPoint examples for visual review."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def rasterize(pdf: Path, output: Path, prefix: str) -> None:
    """Render one PDF to low-resolution PNG pages."""
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["pdftoppm", "-r", "60", "-png", str(pdf), str(output / prefix)],
        check=True,
    )


def main() -> int:
    """Create PDF-page and PPTX-slide thumbnail directories."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--examples", type=Path, default=ROOT / "assets" / "examples"
    )
    parser.add_argument(
        "--out", type=Path, default=ROOT / "assets" / "examples" / "thumbnails"
    )
    parser.add_argument(
        "--format",
        choices=("pdf", "pptx", "both"),
        default="both",
        dest="output_format",
    )
    args = parser.parse_args()
    if not shutil.which("pdftoppm"):
        print("ERROR — pdftoppm is required")
        return 2
    if args.output_format in {"pdf", "both"}:
        pdf_output = args.out / "pdf"
        shutil.rmtree(pdf_output, ignore_errors=True)
        for pdf in sorted(args.examples.glob("*.pdf")):
            rasterize(pdf, pdf_output, pdf.stem)
    pptx_files = (
        sorted(args.examples.glob("*.pptx"))
        if args.output_format in {"pptx", "both"}
        else []
    )
    if pptx_files:
        office = shutil.which("soffice") or shutil.which("libreoffice")
        if not office:
            print("ERROR — LibreOffice is required for PowerPoint thumbnails")
            return 2
        pptx_output = args.out / "pptx"
        shutil.rmtree(pptx_output, ignore_errors=True)
        with tempfile.TemporaryDirectory() as directory_name:
            directory = Path(directory_name)
            for pptx in pptx_files:
                subprocess.run(
                    [
                        office,
                        "--headless",
                        "--convert-to",
                        "pdf",
                        "--outdir",
                        str(directory),
                        str(pptx),
                    ],
                    check=True,
                )
                rasterize(directory / f"{pptx.stem}.pdf", pptx_output, pptx.stem)
    print(f"Wrote thumbnails to {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
