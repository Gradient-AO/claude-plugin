#!/usr/bin/env python3
"""Regression-test orchestrator for the gradient-cio plugin.

Coverage inventory, in execution order:
- static repository and shared-file checks
- report/composer validator regressions
- chart renderer regressions
- connector manifest validation
- connector checker CLI regressions
- PDF renderer fixture regressions (unless --static)
"""

import sys

from suites.harness import fails
from suites.renderer_regressions import render
from suites.static_checks import static


def main():
    a = sys.argv[1:]
    static("--allow-branded" in a)
    if "--static" not in a:
        render("--keep" in a)
    print(f"\n{'ALL PASSED' if not fails else str(len(fails)) + ' FAILED'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
