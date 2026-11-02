#!/usr/bin/env python3
"""Build a Lab model file from a saved get_portfolio_structure (view=allocation_tree) result.

  python3 build_model.py --tree tree.json --name "Total Plan" --label "Gradient Total Plan model" --out model.json

Uses POLICY TARGETS only: target_weight_total_portfolio on leaf sleeves, plus each root class's
target and policy band. Sleeves are mapped to CMA factors with references/sleeve_factor_map.json;
an unmapped sleeve, a missing target or weights that do not sum to 1 stop the build.
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
a = argparse.ArgumentParser()
a.add_argument("--tree", required=True)
a.add_argument("--name", required=True)
a.add_argument("--label", required=True)
a.add_argument("--out", required=True)
a.add_argument("--map", default=os.path.join(HERE, "..", "references", "sleeve_factor_map.json"))
args = a.parse_args()

def load_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


t = load_json(args.tree)
fmap = load_json(args.map)
if (t.get("validation") or {}).get("status") != "passed":
    sys.exit("STOP: structure validation did not pass.")
nodes = t["nodes"]
roots = sorted([n for n in nodes if n.get("parent_id") is None], key=lambda n: n.get("order", 0))
classes = []
for r in roots:
    leaves = [n for n in nodes if n.get("parent_id") == r["allocation_id"] and n.get("is_leaf")]
    sl = []
    for lf in leaves:
        w = lf.get("target_weight_total_portfolio")
        if w is None:
            sys.exit(f"STOP: {lf['allocation_name']!r} has no total-portfolio policy target; the model is incomplete.")
        if lf["allocation_name"] not in fmap:
            sys.exit(f"STOP: no CMA factor mapping for sleeve {lf['allocation_name']!r}. Add it to "
                     "references/sleeve_factor_map.json (proxy=true if approximate).")
        f, px = fmap[lf["allocation_name"]]
        sl.append(dict(name=lf["allocation_name"], weight=w, factor_id=f, proxy=px))
    classes.append(dict(name=r["allocation_name"],
                        target=r.get("target_weight_total_portfolio") or r.get("target_weight"),
                        lower=r.get("lower_limit"), upper=r.get("upper_limit"), sleeves=sl))
tot = sum(s["weight"] for c in classes for s in c["sleeves"])
if abs(tot - 1) > 1e-3:
    sys.exit(f"STOP: leaf policy targets sum to {tot:.4f}, not 1. The model is incomplete or mis-structured.")
p = t["portfolio"]
out = dict(portfolio_id=p["portfolio_id"], name=args.name, model_label=args.label, weights_basis="policy_targets",
           classes=classes, provenance=t.get("provenance"), validation=t.get("validation"))
with open(args.out, "w", encoding="utf-8") as handle:
    json.dump(out, handle, indent=1)
print(f"wrote {args.out}: {len(classes)} classes, {sum(len(c['sleeves']) for c in classes)} sleeves, sum {tot:.6f}")
