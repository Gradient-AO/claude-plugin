#!/usr/bin/env python3
"""Check a saved GradientCIO response against the expected paths in contracts.json.

Usage: python check_contract.py contracts.json <probe_id> response.json
Prints PASS or FAIL with the missing paths; exit code 0 = pass, 1 = fail.
Paths use dots and [n] indexes, e.g. "organizations[0].id". An empty list counts as present.
"""
import json, re, sys

def get(obj, path):
    for part in re.findall(r"[^.\[\]]+|\[\d+\]", path):
        if part.startswith("["):
            i = int(part[1:-1])
            if not isinstance(obj, list) or i >= len(obj):
                return KeyError
            obj = obj[i]
        else:
            if not isinstance(obj, dict) or part not in obj:
                return KeyError
            obj = obj[part]
    return obj

def load(p):
    d = json.load(open(p, encoding="utf-8"))
    if isinstance(d, list) and d and isinstance(d[0], dict) and "text" in d[0]:   # MCP content wrapper
        d = json.loads(d[0]["text"])
    return d

def main():
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    c = json.load(open(sys.argv[1], encoding="utf-8")); pid = sys.argv[2]; resp = load(sys.argv[3])
    probe = next((p for p in c["probes"] if p["id"] == pid), None)
    if not probe:
        raise SystemExit(f"unknown probe {pid}")
    if isinstance(resp, dict) and "error" in resp:
        e = resp["error"]; print(f"FAIL {pid}: error {e.get('code')} http {e.get('http_status')}"); sys.exit(1)
    paths = list(probe["required"]) + (c["envelope"] if probe.get("envelope", True) else [])
    missing = [p for p in paths if get(resp, p) is KeyError]
    if missing:
        print(f"FAIL {pid}: missing {', '.join(missing)}"); sys.exit(1)
    asof = get(resp, "provenance.as_of"); val = get(resp, "validation.status")
    print(f"PASS {pid}" + (f" (as of {asof}" if asof is not KeyError else "") + (f", validation {val})" if val is not KeyError else (")" if asof is not KeyError else "")))

if __name__ == "__main__":
    main()
