#!/usr/bin/env python3
"""Public regression-test orchestrator for the gradient-cio plugin."""

import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from suites.harness import fails
from suites.layout_vocab_contracts import layout_vocab_contracts
from suites.renderer_regressions import render
from suites.static_checks import static


def main():
    args = sys.argv[1:]
    if "--layout-vocab" in args:
        layout_vocab_contracts()
        print(f"\n{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED'}")
        sys.exit(1 if fails else 0)
    static("--allow-branded" in args)
    layout_vocab_contracts()
    if "--static" not in args:
        render("--keep" in args)
    print(f"\n{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
