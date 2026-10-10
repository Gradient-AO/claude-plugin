#!/usr/bin/env python3
"""Copy the canonical shared files into every skill so each skill is self-contained.

Run after any change to a file listed in FILES:
    python tools/sync_shared.py          # sync
    python tools/sync_shared.py --check  # exit 1 if any copy differs (use before packaging)
"""
import hashlib, pathlib, shutil, sys
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = {"shared/gradient_report.py": "scripts/gradient_report.py",
         "shared/gradient_pptx.py": "scripts/gradient_pptx.py",
         "shared/render.py": "scripts/render.py",
         "shared/compose_report.py": "scripts/compose_report.py",
         "shared/check_layout.py": "scripts/check_layout.py",
         "shared/report-style.md": "references/report-style.md",
         "shared/writing-standards.md": "references/writing-standards.md",
         "shared/chart-data.md": "references/chart-data.md",
         "shared/module-scope.md": "references/module-scope.md"}

CHAT_DELIVERY = re.compile(r"^\s+delivery:\s*chat\s*$", re.MULTILINE)


def is_chat_only(skill):
    """Return whether a skill deliberately produces only an in-chat response."""
    return bool(CHAT_DELIVERY.search((skill / "SKILL.md").read_text(encoding="utf-8")))


def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]

def main():
    check = "--check" in sys.argv
    bad = 0
    for skill in sorted((ROOT / "skills").iterdir()):
        if not (skill / "SKILL.md").exists():
            continue
        if is_chat_only(skill):
            continue
        for src, rel in FILES.items():
            s, d = ROOT / src, skill / rel
            if check:
                if not d.exists() or digest(d) != digest(s):
                    print(f"OUT OF SYNC: {skill.name}/{rel}"); bad += 1
            else:
                d.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(s, d)
                print(f"synced {skill.name}/{rel} ({digest(s)})")
    if check:
        print("all copies in sync" if not bad else f"{bad} copies out of sync")
        sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
