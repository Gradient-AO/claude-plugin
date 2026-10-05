#!/usr/bin/env python3
"""Copy the canonical shared files into every skill so each skill is self-contained.

Run after any change to a file listed in FILES:
    python tools/sync_shared.py          # sync
    python tools/sync_shared.py --check  # exit 1 if any copy differs (use before packaging)
"""
import hashlib, pathlib, shutil, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILES = {"shared/gradient_report.py": "scripts/gradient_report.py",
         "shared/report-style.md": "references/report-style.md",
         "shared/chart-data.md": "references/chart-data.md",
         "shared/portfolio-strategy-scope.md": "references/portfolio-strategy-scope.md"}

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()[:12]

def main():
    check = "--check" in sys.argv
    bad = 0
    for skill in sorted((ROOT / "skills").iterdir()):
        if not (skill / "SKILL.md").exists():
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
