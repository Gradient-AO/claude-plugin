#!/usr/bin/env python3
"""Brand this plugin for one client before distributing it.

    python tools/set_branding.py --client "Northwind Pension Plan" --logo path/to/logo.png
    python tools/set_branding.py --client "Northwind Pension Plan" --confidentiality "Confidential — Northwind IC"
    python tools/set_branding.py --reset          # back to Gradient branding

Writes branding.json at the plugin root and copies the logo to assets/client-logo.<ext>.
Logos: PNG or SVG, wide format, transparent or dark-friendly (the cover is dark). Colours never change.
Then repackage the plugin (zip the plugin folder as <name>.plugin).
"""
import argparse, json, pathlib, shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client"); ap.add_argument("--logo"); ap.add_argument("--confidentiality")
    ap.add_argument("--no-powered-by", action="store_true"); ap.add_argument("--reset", action="store_true")
    a = ap.parse_args()
    for old in (ROOT / "assets").glob("client-logo.*"):
        old.unlink()
    b = {"client_name": "", "client_logo": "", "confidentiality": "", "powered_by": True}
    if not a.reset:
        if not a.client:
            ap.error("--client is required (or use --reset)")
        b["client_name"] = a.client
        if a.logo:
            src = pathlib.Path(a.logo)
            if src.suffix.lower() not in (".png", ".svg", ".jpg", ".jpeg"):
                ap.error("logo must be .png, .svg or .jpg")
            (ROOT / "assets").mkdir(exist_ok=True)
            dst = ROOT / "assets" / ("client-logo" + src.suffix.lower())
            shutil.copyfile(src, dst); b["client_logo"] = f"assets/{dst.name}"
        b["confidentiality"] = a.confidentiality or ""
        b["powered_by"] = not a.no_powered_by
    (ROOT / "branding.json").write_text(json.dumps(b, indent=2) + "\n")
    print("branding:", json.dumps(b))

if __name__ == "__main__":
    main()
