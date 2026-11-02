"""Spec engine for spec-driven Gradient + Claude showcase posts.

A post spec is a JSON file. Words (headline, analysis, labels) are typed by Claude.
Every NUMBER is a reference into a saved Gradient payload, so it is read, never typed.

Inputs:   "inputs": {"rr": "path/to/relative_returns.json", "cma": "path/to/cma.json"}
Ref:      {"ref": "rr:board_total[pair_id=growth_vs_value].relative_3m_pct", "fmt": "pct1"}
Derived:  {"op": "sub", "args": [ref, ref], "scale": 100, "fmt": "pp1"}   ops: sub add mul div
Text ref: {"ref": "regime:regions[region=NA].latest.label", "fmt": "title"}
Literal text (no number): {"text": "n/a"}

Path syntax: dot keys, [n] list index, [key=value] first list item whose key equals value.
Formats: pct1 (value already in %), pct0, x100pct1 / x100pct0 (decimal -> %), pp1 (percentage
points), int, num2, prob0 (decimal probability -> %), date (ISO -> Oct 21, 2026), ord (95 -> 95th), title, text.
"""
import json, os, re, sys

_SEG = re.compile(r"([^.\[\]]+)|\[(\d+)\]|\[([^=\]]+)=([^\]]+)\]")


def load_inputs(inputs, base_dir="."):
    data, meta = {}, {}
    for key, path in inputs.items():
        p = path if os.path.isabs(path) else os.path.join(base_dir, path)
        with open(p, encoding="utf-8") as fh:
            d = json.load(fh)
        status = (d.get("validation") or {}).get("status")
        if status is not None and status != "passed":
            sys.exit(f"STOP: input {key!r} validation.status is {status!r}, not 'passed'. Do not publish.")
        data[key] = d
        prov = d.get("provenance") or {}
        meta[key] = {
            "file": p,
            "validation_status": status,
            "provenance_as_of": prov.get("as_of"),
            "source_as_of": prov.get("source_as_of"),
            "methodology_ref": (prov.get("method") or {}).get("methodology_ref"),
            "payload_digest": ((prov.get("reproducibility") or {}).get("payload_digest") or "")[:12],
            "data_scope": (prov.get("data_scope") or {}).get("label"),
        }
    return data, meta


def get_path(obj, path):
    cur = obj
    for m in _SEG.finditer(path):
        key, idx, fk, fv = m.groups()
        if key is not None:
            if not isinstance(cur, dict) or key not in cur:
                raise KeyError(f"missing key {key!r} in path {path!r}")
            cur = cur[key]
        elif idx is not None:
            cur = cur[int(idx)]
        else:
            hit = [x for x in cur if isinstance(x, dict) and str(x.get(fk)) == fv]
            if not hit:
                raise KeyError(f"no item with {fk}={fv} in path {path!r}")
            cur = hit[0]
    return cur


def resolve(node, data):
    """Return the raw value of a ref / derived / literal node."""
    if node is None:
        return None
    if "text" in node:
        return node["text"]
    if "ref" in node:
        src, _, path = node["ref"].partition(":")
        if src not in data:
            raise KeyError(f"unknown input {src!r} in ref {node['ref']!r}")
        v = get_path(data[src], path)
    elif "op" in node:
        a, b = (resolve(x, data) for x in node["args"])
        v = {"sub": a - b, "add": a + b, "mul": a * b, "div": a / b}[node["op"]]
    else:
        raise ValueError(f"node has no ref, op or text: {node}")
    if isinstance(v, (int, float)) and not isinstance(v, bool) and node.get("scale"):
        v = v * node["scale"]
    return v


def fmt(v, f="text", sign=None):
    if v is None:
        return "—"
    if f in ("text",):
        return str(v)
    if f == "date":
        from datetime import date as _d
        parsed = _d.fromisoformat(str(v)[:10])
        return f"{parsed.strftime('%b')} {parsed.day}, {parsed.year}"
    if f == "title":
        return str(v).replace("_", " ").title()
    if f in ("x100pct1", "x100pct0"):
        v, f = v * 100, "pct1" if f.endswith("1") else "pct0"
    if f == "ord":
        n = int(round(v))
        suf = "th" if 10 <= n % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
        return f"{n}{suf}"
    if f == "prob0":
        return f"{v * 100:.0f}%"
    signed = True if sign is None and f in ("pct1", "pct0", "pp1") else bool(sign)
    if f == "pct1":
        s = f"{v:+.1f}%" if signed else f"{v:.1f}%"
    elif f == "pct0":
        s = f"{v:+.0f}%" if signed else f"{v:.0f}%"
    elif f == "pp1":
        s = f"{v:+.1f} pp"
    elif f == "int":
        s = f"{v:.0f}"
    elif f == "num2":
        s = f"{v:.2f}"
    else:
        s = str(v)
    return s.replace("-", "−")


def value(node, data):
    """(display string, raw value) for a node, honoring its fmt and sign settings."""
    raw = resolve(node, data)
    return fmt(raw, node.get("fmt", "text"), node.get("sign")), raw


def facts_dump(spec, data, meta):
    """Resolve every node in the spec so Claude can check the numbers before rendering."""
    out = {"inputs": meta, "values": []}

    def walk(x, where):
        if isinstance(x, dict):
            if any(k in x for k in ("ref", "op", "text")) and not isinstance(x.get("text", ""), dict):
                try:
                    s, raw = value(x, data)
                    out["values"].append({"at": where, "display": s, "raw": raw})
                except Exception as e:  # report, don't hide
                    out["values"].append({"at": where, "error": str(e)})
                return
            for k, v in x.items():
                walk(v, f"{where}.{k}")
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, f"{where}[{i}]")
    walk({k: v for k, v in spec.items() if k not in ("inputs",)}, "spec")
    return out
