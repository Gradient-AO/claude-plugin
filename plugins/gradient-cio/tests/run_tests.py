#!/usr/bin/env python3
"""Public regression-test orchestrator for the gradient-cio plugin."""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from suites.harness import fails
from suites.renderer_regressions import render
from suites.static_checks import static


def main():
    args = sys.argv[1:]
    static("--allow-branded" in args)
    if "--static" not in args:
        render("--keep" in args)
    print(f"\n{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
