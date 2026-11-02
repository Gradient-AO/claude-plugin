#!/usr/bin/env python3
"""Copy the shared Quick Take kit into each Quick Take skill, or check that the copies match (CI).

  python3 tools/sync_quicktake_shared.py          # write the copies
  python3 tools/sync_quicktake_shared.py --check  # exit 1 if any copy differs (use in CI and before release)

Only the skills in QUICKTAKE_SKILLS are touched; the report skills keep their own shared files.

Why copies: each skill folder must stay self-contained when it is installed, so it carries its own
scripts/brand.py, assets/fonts, assets/logos and references/canvas-spec.md. quicktake-shared/ is the only place to edit them.
"""
import filecmp
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, "quicktake-shared")
QUICKTAKE_SKILLS = [
    "gradient-portfolio-lens",
    "gradient-signal-spotlight",
    "gradient-risk-pulse",
    "gradient-tactical-dashboard",
    "gradient-ask-gradient",
]
SKILLS = os.path.join(ROOT, "skills")
# shared path -> destination inside each skill
MAP = [
    ("brand.py", "scripts/brand.py"),
    ("canvas-spec.md", "references/canvas-spec.md"),
    ("fonts", "assets/fonts"),
    ("logos", "assets/logos"),
]
RETIRED = ["references/brand.md"]  # replaced by canvas-spec.md


def files(src):
    if os.path.isfile(src):
        yield "", src
        return
    for d, _, fs in os.walk(src):
        for f in fs:
            p = os.path.join(d, f)
            yield os.path.relpath(p, src), p


def main(check):
    drift = []
    skills = [d for d in QUICKTAKE_SKILLS if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md"))]
    missing = sorted(set(QUICKTAKE_SKILLS) - set(skills))
    if missing:
        print("WARNING: Quick Take skills not found: " + ", ".join(missing))
    for sk in skills:
        for src_rel, dst_rel in MAP:
            src = os.path.join(SHARED, src_rel)
            for rel, sp in files(src):
                dp = os.path.join(SKILLS, sk, dst_rel, rel) if rel else os.path.join(SKILLS, sk, dst_rel)
                same = os.path.isfile(dp) and filecmp.cmp(sp, dp, shallow=False)
                if not same:
                    drift.append(os.path.relpath(dp, ROOT))
                    if not check:
                        os.makedirs(os.path.dirname(dp), exist_ok=True)
                        shutil.copy2(sp, dp)
        for r in RETIRED:
            p = os.path.join(SKILLS, sk, r)
            if os.path.exists(p):
                drift.append(os.path.relpath(p, ROOT) + " (retired)")
                if not check:
                    os.remove(p)
    if check:
        if drift:
            print(
                "Shared files out of sync:\n  "
                + "\n  ".join(drift)
                + "\nRun: python3 tools/sync_quicktake_shared.py"
            )
            sys.exit(1)
        print(f"OK: {len(skills)} Quick Take skills match quicktake-shared/.")
    else:
        print(
            f"Synced {len(skills)} skills; {len(drift)} file(s) updated."
            if drift
            else "Already in sync."
        )


if __name__ == "__main__":
    main("--check" in sys.argv)
