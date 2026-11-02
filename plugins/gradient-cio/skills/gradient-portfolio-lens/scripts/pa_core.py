"""Gradient Portfolio Lens core engine (formerly the PA core shared by the gradient-pa-* skills).

The MCP is the source of truth for every published number: build the CMA file from MCP payloads
(build_cma_mcp.py) and cross-check each post against get_capital_market_assumptions view=portfolio_analytics
(mcp_check.py). This engine adds the scenario sweeps, moves and gates the MCP does not compute.

Inputs (all saved Gradient data):
  cma      Gradient ICAPM capital market assumptions: factor excess returns, volatilities, correlations,
           house (policy) vols for private markets, the USD Index factor and cash rates by currency.
  regimes  Gradient's regime overlays (multipliers, add-ons, persistence) for the same CMA release.
  models   Gradient model portfolios as POLICY TARGET weights (never holdings).

Every number in a post is computed here from those inputs.
"""
import copy, json, os, sys
import numpy as np

PA_CORE_VERSION = "3.0.0"
import datetime as _dt
HERE = os.path.dirname(os.path.abspath(__file__))
PRIVATE_FACTORS = {12, 13, 14, 15, 16}
CURRENT_REGIME_MAX_AGE_DAYS = 45
EQUITY_FACTORS = {1, 4, 5, 6}
BOND_FACTORS = {7, 8}

# ----------------------------------------------------------------------------- portfolio library
# Reference portfolios built directly from Gradient CMA factors. Weights are printed on every image.
# "Global Public Equity" = Gradient's house global equity mix from its Global Public Equity model:
# 80% developed markets (factor 1) and 20% emerging markets (factor 6). Never use index-provider names.
GPE_DM, GPE_EM = 0.80, 0.20
GPE_NOTE = "Global Public Equity = 80% developed / 20% emerging (Gradient Global Public Equity model split)"


def _gpe(eq, bonds, bond_factor=7, bond_name="Global Aggregate Bonds", cash=0.0):
    rows = [("Global Public Equity", [("Developed Equity", eq * GPE_DM, 1), ("Emerging Equity", eq * GPE_EM, 6)]),
            (bond_name, [(bond_name, bonds, bond_factor)])]
    if cash:
        rows.append(("Cash", [("Cash", cash, 9)]))
    return rows


LIBRARY = {
    "global_60_40": ("Global 60/40", _gpe(0.60, 0.40)),
    "global_70_30": ("Global 70/30", _gpe(0.70, 0.30)),
    "global_50_50": ("Global 50/50", _gpe(0.50, 0.50)),
    "global_40_60": ("Global 40/60", _gpe(0.40, 0.60)),
    "global_80_20": ("Global 80/20", _gpe(0.80, 0.20)),
    "global_60_40_govt": ("Global 60/40 with Government Bonds", _gpe(0.60, 0.40, 8, "Global Government Bonds")),
    "global_60_30_10": ("Global 60/30/10 with Cash", _gpe(0.60, 0.30, cash=0.10)),
    "dm_60_40": ("Developed-Markets 60/40", [("Developed Equity", [("Developed Equity", 0.60, 1)]),
                                            ("Global Aggregate Bonds", [("Global Aggregate Bonds", 0.40, 7)])]),
}

# Common allocator ARCHETYPES. Stylized weights defined by Gradient for illustration; they are NOT peer data,
# survey averages or any institution's portfolio. Every image prints the weights and ARCHETYPE_NOTE.
ARCHETYPE_NOTE = "Gradient illustrative archetype: stylized weights, not peer or survey data"


def _gpe_cls(w):
    return ("Global Public Equity", [("Developed Equity", w * GPE_DM, 1), ("Emerging Equity", w * GPE_EM, 6)])


ARCHETYPES = {
    "endowment_style": ("Endowment-Style", [
        _gpe_cls(0.30), ("Fixed Income", [("Global Government Bonds", 0.08, 8)]),
        ("Private Equity", [("Private Equity", 0.20, 13), ("Venture Capital", 0.08, 14)]),
        ("Hedge Funds", [("Hedge Funds", 0.18, 17)]),
        ("Real Assets", [("Real Estate", 0.08, 12), ("Infrastructure", 0.05, 16)]),
        ("Cash", [("Cash", 0.03, 9)])]),
    "public_pension_style": ("Public-Pension-Style", [
        _gpe_cls(0.45), ("Fixed Income", [("Global Aggregate Bonds", 0.22, 7)]),
        ("Private Equity", [("Private Equity", 0.13, 13)]),
        ("Private Credit", [("Direct Lending", 0.05, 15)]),
        ("Real Assets", [("Real Estate", 0.09, 12), ("Infrastructure", 0.03, 16)]),
        ("Hedge Funds", [("Hedge Funds", 0.03, 17)])]),
    "foundation_70_30_alts": ("Foundation 70/30 with Alternatives", [
        _gpe_cls(0.55), ("Fixed Income", [("Global Aggregate Bonds", 0.20, 7)]),
        ("Alternatives", [("Hedge Funds", 0.10, 17), ("Private Equity", 0.10, 13)]),
        ("Real Assets", [("Real Estate", 0.05, 12)])]),
    "60_40_plus_alts": ("50/30/20 (60/40 plus Alternatives)", [
        _gpe_cls(0.50), ("Fixed Income", [("Global Aggregate Bonds", 0.30, 7)]),
        ("Alternatives", [("Private Equity", 0.07, 13), ("Hedge Funds", 0.05, 17)]),
        ("Real Assets", [("Real Estate", 0.05, 12), ("Infrastructure", 0.03, 16)])]),
    "all_weather_style": ("All-Weather-Style", [
        _gpe_cls(0.30), ("Government Bonds", [("Global Government Bonds", 0.55, 8)]),
        ("Real Assets", [("Gold", 0.075, 19), ("Commodities", 0.075, 18)])]),
}

# Assumptions Gradient's CMA team has not yet confirmed. Posts that lean on them carry a visible caveat line,
# and the diversifier scorecard leaves them out unless the spec opts in (include_under_review: true).
UNDER_REVIEW = {
    19: "Gold: volatility is a round 12% and its correlation with developed equity (0.52) is high versus history",
    16: "Infrastructure: expected return over cash (1.86%) sits below High Yield; confirm before ranking it",
}


def library_portfolio(key):
    if key in ARCHETYPES:
        name, classes = ARCHETYPES[key]
        kind, label, note = "archetype", f"{name} (illustrative archetype)", ARCHETYPE_NOTE
    elif key in LIBRARY:
        name, classes = LIBRARY[key]
        kind, label, note = "reference", f"{name} (reference portfolio)", None
    else:
        sys.exit(f"STOP: unknown library portfolio {key!r}. Options: {', '.join(list(LIBRARY) + list(ARCHETYPES))}")
    uses_gpe = any(c == "Global Public Equity" for c, _ in classes)
    if uses_gpe:
        note = "; ".join(x for x in (note, GPE_NOTE) if x)
    return dict(name=name, model_label=label, weights_basis="policy_targets",
                kind=kind, note=note,
                classes=[dict(name=c, target=sum(w for _, w, _ in sl), lower=None, upper=None,
                              sleeves=[dict(name=n, weight=w, factor_id=f, proxy=False) for n, w, f in sl])
                         for c, sl in classes],
                validation={"status": "passed"})


def load_portfolio(ref, base_dir):
    """ref = 'lib:<key>' for a reference portfolio, or a path to a model file built by build_model.py."""
    if ref.startswith("lib:"):
        return library_portfolio(ref[4:])
    p = ref if os.path.isabs(ref) else os.path.join(base_dir, ref)
    with open(p, encoding="utf-8") as handle:
        m = json.load(handle)
    m.setdefault("kind", "model")
    return m


# ----------------------------------------------------------------------------- gate
def caveats_for(*ids):
    """Under-review notes for the factors a post uses."""
    return [UNDER_REVIEW[i] for i in sorted(set(ids)) if i in UNDER_REVIEW]


def gate(model, cma):
    for name, d in (("portfolio", model), ("cma", cma)):
        if (d.get("validation") or {}).get("status") != "passed":
            sys.exit(f"STOP: {name} validation.status is not 'passed'.")
        if d.get("synthetic_data") or (d.get("source_provenance") or {}).get("synthetic_data"):
            sys.exit(f"STOP: {name} is synthetic data. Never publish synthetic or demo series.")
    if model.get("weights_basis") != "policy_targets":
        sys.exit("STOP: weights must be policy targets. Gradient model holdings are fictional demo funds.")
    tot = sum(s["weight"] for c in model["classes"] for s in c["sleeves"])
    if abs(tot - 1) > 1e-4:
        sys.exit(f"STOP: weights sum to {tot:.6f}, not 1.")
    ids = {f["factor_id"] for f in cma["factors"]}
    for c in model["classes"]:
        for s in c["sleeves"]:
            if s["factor_id"] not in ids:
                sys.exit(f"STOP: factor {s['factor_id']} for {s['name']} is not in the CMA file.")


# ----------------------------------------------------------------------------- scenarios
SCENARIO_LABELS = {
    "baseline": "Baseline",
    "regime:RECOVERY": "Recovery", "regime:REFLATION": "Reflation", "regime:LATE_CYCLE": "Late Cycle",
    "regime:STAGFLATION": "Stagflation", "regime:CONTRACTION": "Contraction",
    "regime:SYSTEMIC_STRESS": "Systemic Stress", "regime:DISINFLATIONARY_GROWTH": "Disinflationary Growth",
    "regime:current": "Current Regime",
    "whatif:stock_bond_corr_+0.4": "Stock–Bond Sync",
    "sensitivity:private_vols_house": "Private Vols at House Level",
}
SCENARIO_KIND = {"baseline": "Gradient baseline", "regime": "Gradient regime overlay",
                 "whatif": "what-if on Gradient assumptions (not a Gradient forecast)",
                 "sensitivity": "sensitivity check"}


def apply_scenario(cma, regimes, scen):
    """Return (scenario_cma, meta). Never mutates the input."""
    c = copy.deepcopy(cma)
    kind = scen.split(":")[0]
    meta = dict(id=scen, label=SCENARIO_LABELS.get(scen, scen), kind=SCENARIO_KIND.get(kind, kind))
    if scen == "baseline":
        return c, meta
    if kind == "regime":
        rid = scen.split(":", 1)[1]
        if rid == "current":
            cm = regimes.get("current_mapping") or {}
            asof = cm.get("as_of")
            if not asof:
                sys.exit("STOP: regimes.current_mapping has no as_of date. Refresh it from get_macro_signals "
                         "(view grip_cma_statistics, or regime_state once publishing resumes) before using regime:current.")
            age = (_dt.date.today() - _dt.date.fromisoformat(asof)).days
            if age > CURRENT_REGIME_MAX_AGE_DAYS:
                sys.exit(f"STOP: the current-regime mapping is {age} days old (as of {asof}; limit "
                         f"{CURRENT_REGIME_MAX_AGE_DAYS}). Refresh it, or name the regime explicitly instead of regime:current.")
            rid = cm["regime"]
            meta["label"] = f"Current Regime ({SCENARIO_LABELS['regime:' + rid]})"
            meta["note"] = (f"GRIP {regimes['current_mapping']['grip']} ({regimes['current_mapping']['stance']}) "
                            f"maps to {rid} in Gradient's method")
        if regimes.get("compatible_cma_release") != cma["release"]["version"]:
            sys.exit("STOP: regime overlays are not compatible with this CMA release.")
        r = regimes["regimes"][rid]
        w = min(r["persistence_years"], regimes["horizon_years"]) / regimes["horizon_years"]
        for f in c["factors"]:
            a = r["adjustments"].get(str(f["factor_id"]))
            if not a:
                continue
            add = a["returnAdd"] or 0.0
            f["excess_return"] = f["excess_return"] * ((1 - w) + w * a["returnMult"]) + w * add
            f["volatility"] = f["volatility"] * ((1 - w) + w * a["volMult"] ** 2) ** 0.5
        meta["horizon_weight"] = w
        meta["persistence_years"] = r["persistence_years"]
        meta["short_label"] = meta["label"]
        meta["label"] = f"{meta['label']} ({r['persistence_years']:g} of {regimes['horizon_years']} yrs)"
        return c, meta
    if scen == "whatif:stock_bond_corr_+0.4":
        for p in c["correlations"]:
            if ({p["a"], p["b"]} & EQUITY_FACTORS) and ({p["a"], p["b"]} & BOND_FACTORS) and not (
                    {p["a"], p["b"]} <= EQUITY_FACTORS or {p["a"], p["b"]} <= BOND_FACTORS):
                p["rho"] = 0.4
        meta["note"] = "equity–bond correlations set to +0.4, all else unchanged"
        return c, meta
    if scen == "sensitivity:private_vols_house":
        for f in c["factors"]:
            if f["factor_id"] in PRIVATE_FACTORS and f.get("volatility_policy"):
                f["volatility"] = f["volatility_policy"]
        meta["note"] = "private-market volatilities at Gradient's house (policy) level; correlations unchanged"
        return c, meta
    sys.exit(f"STOP: unknown scenario {scen!r}. Options: {', '.join(SCENARIO_LABELS)}")


# ----------------------------------------------------------------------------- engine
class Engine:
    def __init__(self, cma, factors=None):
        """factors: optional set of factor ids to use (the portfolio's own); keeps what-if matrices valid."""
        self.ids = [f["factor_id"] for f in cma["factors"] if factors is None or f["factor_id"] in factors]
        self.mu = {f["factor_id"]: f["excess_return"] for f in cma["factors"] if f["factor_id"] in self.ids}
        self.vol = {f["factor_id"]: f["volatility"] for f in cma["factors"] if f["factor_id"] in self.ids}
        self.fname = {f["factor_id"]: f["name"] for f in cma["factors"] if f["factor_id"] in self.ids}
        n = len(self.ids)
        R = np.eye(n)
        for p in cma["correlations"]:
            if p["a"] in self.ids and p["b"] in self.ids:
                i, j = self.ids.index(p["a"]), self.ids.index(p["b"])
                R[i, j] = R[j, i] = p["rho"]
        if np.linalg.eigvalsh(R).min() < -1e-9:
            sys.exit("STOP: scenario correlation matrix is not positive semidefinite.")
        D = np.diag([self.vol[f] for f in self.ids])
        self.S = D @ R @ D
        self.cash = cma.get("usd_cash_rate", 0.0)

    @staticmethod
    def sleeves(model):
        return [dict(cls=c["name"], **s) for c in model["classes"] for s in c["sleeves"]]

    def stats(self, sl):
        w = np.zeros(len(self.ids))
        for s in sl:
            w[self.ids.index(s["factor_id"])] += s["weight"]
        Sw = self.S @ w
        sig = float(w @ Sw) ** 0.5
        mu = float(sum(s["weight"] * self.mu[s["factor_id"]] for s in sl))
        rows, cls = [], {}
        for s in sl:
            k = self.ids.index(s["factor_id"])
            mr = Sw[k] / sig
            rows.append(dict(name=s["name"], cls=s["cls"], weight=s["weight"], factor_id=s["factor_id"],
                             proxy=s.get("proxy", False), exp_excess=self.mu[s["factor_id"]],
                             vol=self.vol[s["factor_id"]], marginal_risk=mr, risk_share=s["weight"] * mr / sig))
        for r in rows:
            c = cls.setdefault(r["cls"], dict(name=r["cls"], weight=0.0, risk_share=0.0))
            c["weight"] += r["weight"]; c["risk_share"] += r["risk_share"]
        div = sum(r["weight"] * r["vol"] for r in rows) / sig
        return dict(exp_excess=mu, exp_total=mu + self.cash, vol=sig, ret_per_risk=mu / sig,
                    diversification_ratio=div, sleeves=rows, classes=list(cls.values()))

    def move(self, model, frm, to, amount):
        sl = [dict(s) for s in self.sleeves(model)]
        pick = lambda lab: [s for s in sl if s["name"] == lab] or [s for s in sl if s["cls"] == lab]
        src, dst = pick(frm), pick(to)
        if not src or not dst:
            sys.exit(f"STOP: unknown sleeve or class in move: {frm!r} -> {to!r}")
        sw = sum(s["weight"] for s in src)
        if amount > sw + 1e-12:
            sys.exit(f"STOP: cannot move {amount:.1%} from {frm} (only {sw:.1%}).")
        for s in src:
            s["weight"] -= amount * s["weight"] / sw
        dw = sum(s["weight"] for s in dst)
        for s in dst:
            s["weight"] += amount * (s["weight"] / dw if dw > 0 else 1 / len(dst))
        return sl

    def add(self, sl, target, step):
        sl = [dict(x) for x in sl]
        tgt = [x for x in sl if x["name"] == target] or [x for x in sl if x["cls"] == target]
        tw = sum(x["weight"] for x in tgt)
        rest = 1 - tw
        for x in sl:
            if any(x is t for t in tgt):
                x["weight"] += step * (x["weight"] / tw if tw > 0 else 1 / len(tgt))
            else:
                x["weight"] *= (rest - step) / rest
        return sl

    def marginal(self, model, step=0.01, level="class"):
        sl = self.sleeves(model)
        base = self.stats(sl)
        names = [c["name"] for c in model["classes"]] if level == "class" else [x["name"] for x in sl]
        out = []
        for n in names:
            a = self.stats(self.add(sl, n, step))
            dr, dv = a["exp_excess"] - base["exp_excess"], a["vol"] - base["vol"]
            w = sum(x["weight"] for x in sl if (x["cls"] if level == "class" else x["name"]) == n)
            out.append(dict(name=n, weight=w, marginal_return=dr, marginal_risk=dv,
                            d_ret_per_risk=a["ret_per_risk"] - base["ret_per_risk"]))
        return dict(step=step, level=level, rows=out, base_ret_per_risk=base["ret_per_risk"])

    @staticmethod
    def band_check(model, sl):
        out = []
        for c in model["classes"]:
            w = sum(s["weight"] for s in sl if s["cls"] == c["name"])
            lo, hi = c.get("lower"), c.get("upper")
            out.append(dict(name=c["name"], weight=w, lower=lo, upper=hi,
                            within=(lo is None or w >= lo - 1e-9) and (hi is None or w <= hi + 1e-9)))
        return out


def summarize(st):
    return dict(exp_excess=st["exp_excess"], exp_total=st["exp_total"], vol=st["vol"],
                ret_per_risk=st["ret_per_risk"],
                classes=[{k: c[k] for k in ("name", "weight", "risk_share")} for c in st["classes"]])


def factors_of(*models):
    return {s["factor_id"] for m in models for c in m["classes"] for s in c["sleeves"]}


def run(model, cma, regimes, scenario, factors=None):
    c, meta = apply_scenario(cma, regimes, scenario)
    E = Engine(c, factors or factors_of(model))
    return E, summarize(E.stats(E.sleeves(model))), meta


# ----------------------------------------------------------------------------- currency lens
CURRENCY_FACTORS = {1, 6, 7, 8, 9}


def currency_gate(cma):
    """The currency lens stays blocked until the two open data questions are answered and recorded in the CMA file:
      fx.expected_change_basis: "spot" (USD spot change only) or "excess" (currency excess return incl. carry)
      fx.usd_share: {factor_id: share of that factor's exposure denominated in USD} for every factor used."""
    fx = cma.get("fx") or {}
    if fx.get("expected_change_basis") not in ("spot", "excess"):
        sys.exit("STOP: currency lens blocked. Confirm with Gradient whether the USD Index expected change is a spot "
                 "change or a currency excess return (incl. carry), then set fx.expected_change_basis in the CMA file.")
    if not fx.get("usd_share"):
        sys.exit("STOP: currency lens blocked. Set fx.usd_share (USD-denominated share of each factor, from Gradient "
                 "data) so only dollar exposure carries dollar risk.")


def currency_view(model, cma, home, hedge_ratio):
    """Expected excess return over HOME cash and volatility for a home-currency investor hedging `hedge_ratio`
    of the portfolio's DOLLAR exposure. Dollar exposure = sum of weights x USD share of each factor.
      spot basis:   E = mu + x*(r_usd - r_home) + (1-h)*x*E[fx_spot]              (hedged share earns cash parity)
      excess basis: E = mu + (1-h)*x*E[fx_excess]                                (carry already inside the factor)
      Var = w'Sw + ((1-h)x)^2 s_fx^2 + 2 (1-h) * sum_i w_i u_i s_i s_fx rho_i,fx
    (mu is excess over USD cash; for the spot basis the USD-cash leg is converted at parity on the hedged share.)"""
    currency_gate(cma)
    fx = cma["fx"]
    share = {int(k): v for k, v in fx["usd_share"].items()}
    for s_ in Engine.sleeves(model):
        if s_["factor_id"] not in CURRENCY_FACTORS:
            sys.exit("STOP: the currency lens supports Developed Equity, Emerging Equity, Global Aggregate Bonds, "
                     "Global Government Bonds and Cash only.")
        if s_["factor_id"] not in share:
            sys.exit(f"STOP: fx.usd_share has no entry for factor {s_['factor_id']}.")
    E = Engine(cma, factors_of(model))
    sl = E.sleeves(model)
    st = E.stats(sl)
    r_usd, r_home = cma["cash_rates"]["USD"], cma["cash_rates"][home]
    if home == "USD":
        return dict(home=home, hedge_ratio=0.0, exp_excess=st["exp_excess"], vol=st["vol"],
                    ret_per_risk=st["ret_per_risk"], fx_share_of_variance=0.0, carry=0.0, usd_exposure=0.0)
    x = sum(s_["weight"] * share[s_["factor_id"]] for s_ in sl)
    h, e = hedge_ratio, (1 - hedge_ratio)
    if fx["expected_change_basis"] == "spot":
        mu = st["exp_excess"] + (r_usd - r_home) + e * x * fx["expected_change"]
    else:
        mu = st["exp_excess"] + e * x * fx["expected_change"] - (1 - x) * 0.0
    cov = sum(s_["weight"] * share[s_["factor_id"]] * E.vol[s_["factor_id"]] * fx["volatility"] *
              fx["correlations"].get(str(s_["factor_id"]), 0.0) for s_ in sl)
    var = st["vol"] ** 2 + (e * x) ** 2 * fx["volatility"] ** 2 + 2 * e * cov
    vol = var ** 0.5
    return dict(home=home, hedge_ratio=h, exp_excess=mu, vol=vol, ret_per_risk=mu / vol,
                fx_share_of_variance=((e * x) ** 2 * fx["volatility"] ** 2 + 2 * e * cov) / var,
                carry=h * x * (r_home - r_usd), usd_exposure=x)
