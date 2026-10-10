#!/usr/bin/env python3
"""Compare rendered page/slide thumbnails against committed references."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageChops


def difference_ratio(reference: Path, actual: Path) -> float:
    """Return the share of pixels that differ in either image."""
    with Image.open(reference).convert("RGB") as expected, Image.open(actual).convert(
        "RGB"
    ) as observed:
        if expected.size != observed.size:
            return 1.0
        difference = ImageChops.difference(expected, observed)
        histogram = difference.convert("L").point(lambda value: 255 if value else 0)
        changed = sum(histogram.histogram()[1:])
        return changed / (expected.width * expected.height)


def main() -> int:
    """Check every committed PNG against the matching generated PNG."""
    parser = argparse.ArgumentParser()
    parser.add_argument("reference", type=Path)
    parser.add_argument("actual", type=Path)
    parser.add_argument("--threshold", type=float, default=0.02)
    args = parser.parse_args()
    references = sorted(args.reference.rglob("*.png"))
    actuals = sorted(args.actual.rglob("*.png"))
    failures: list[str] = []
    if not references:
        print("ERROR — no reference thumbnails found")
        return 2
    reference_names = {
        path.relative_to(args.reference).as_posix() for path in references
    }
    actual_names = {path.relative_to(args.actual).as_posix() for path in actuals}
    for extra in sorted(actual_names - reference_names):
        failures.append(f"{extra}: unexpected generated image")
    for reference in references:
        relative = reference.relative_to(args.reference)
        actual = args.actual / relative
        if not actual.is_file():
            failures.append(f"{relative}: generated image is missing")
            continue
        ratio = difference_ratio(reference, actual)
        if ratio > args.threshold:
            failures.append(
                f"{relative}: {ratio:.2%} of pixels differ "
                f"(limit {args.threshold:.2%})"
            )
    if failures:
        print(f"FAIL — {len(failures)} visual regression(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print(f"PASS — {len(references)} visual references within tolerance")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
