#!/usr/bin/env python3
"""Copy the shared Quick Take kit into each Quick Take skill, or check that the copies match (CI).

  python plugins/gradient-cio/tools/sync_quicktake_shared.py          # write the copies
  python plugins/gradient-cio/tools/sync_quicktake_shared.py --check  # exit 1 if any copy differs

Only the skills in QUICKTAKE_SKILLS are touched; the report skills keep their own shared files.

Why copies: each skill folder must stay self-contained when it is installed, so it carries its own
scripts/brand.py, assets/fonts, assets/logos, references/canvas-spec.md, and (for spec-driven
skills) scripts/spec.py and references/spec_format.md. quicktake-shared/ is the only place to edit them.
"""

from __future__ import annotations

import pathlib
import shutil
import sys

if str(pathlib.Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from _common import CANVAS_RENDERERS, PLUGIN_ROOT, SKILLS_DIR, normalized_digest

ROOT = PLUGIN_ROOT
SHARED = ROOT / "quicktake-shared"
SKILLS = SKILLS_DIR
QUICKTAKE_SKILLS = tuple(CANVAS_RENDERERS.keys())
SPEC_SKILLS = frozenset(
    {
        "gradient-tactical-dashboard",
        "gradient-ask-gradient",
    }
)
# shared path -> destination inside each Quick Take skill
MAP = (
    ("brand.py", "scripts/brand.py"),
    ("canvas-spec.md", "references/canvas-spec.md"),
    ("fonts", "assets/fonts"),
    ("logos", "assets/logos"),
)
# shared path -> destination inside spec-driven Quick Take skills
SPEC_MAP = (
    ("spec.py", "scripts/spec.py"),
    ("spec_format.md", "references/spec_format.md"),
)
RETIRED = ("references/brand.md",)  # replaced by canvas-spec.md


def files(src: pathlib.Path):
    if src.is_file():
        yield pathlib.Path(), src
        return
    for path in sorted(src.rglob("*")):
        if path.is_file():
            yield path.relative_to(src), path


def main(check: bool) -> int:
    drift: list[str] = []
    skills = [
        name for name in QUICKTAKE_SKILLS if (SKILLS / name / "SKILL.md").is_file()
    ]
    missing = sorted(set(QUICKTAKE_SKILLS) - set(skills))
    if missing:
        print("WARNING: Quick Take skills not found: " + ", ".join(missing))
    for sk in skills:
        skill_mappings = list(MAP)
        if sk in SPEC_SKILLS:
            skill_mappings.extend(SPEC_MAP)
        for src_rel, dst_rel in skill_mappings:
            src = SHARED / src_rel
            for rel, sp in files(src):
                dp = (
                    SKILLS / sk / dst_rel / rel
                    if str(rel) != "."
                    else SKILLS / sk / dst_rel
                )
                same = dp.is_file() and normalized_digest(sp) == normalized_digest(dp)
                if not same:
                    drift.append(dp.relative_to(ROOT).as_posix())
                    if not check:
                        dp.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(sp, dp)
        for retired_rel in RETIRED:
            retired_path = SKILLS / sk / retired_rel
            if retired_path.exists():
                drift.append(retired_path.relative_to(ROOT).as_posix() + " (retired)")
                if not check:
                    retired_path.unlink()
    if check:
        if drift:
            print(
                "Shared files out of sync:\n  "
                + "\n  ".join(drift)
                + "\nRun: python plugins/gradient-cio/tools/sync_quicktake_shared.py"
            )
            return 1
        print(f"OK: {len(skills)} Quick Take skills match quicktake-shared/.")
        return 0
    print(
        f"Synced {len(skills)} skills; {len(drift)} file(s) updated."
        if drift
        else "Already in sync."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main("--check" in sys.argv))
