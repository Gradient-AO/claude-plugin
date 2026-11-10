---
name: "gradient-pa-marginal"
description: "Gradient PA · Marginal: marginal return and marginal risk of adding 1% to each asset class (quadrant chart with an efficiency line), the risk mix before and after a specific move (for example 5% from Public Equity to Private Debt), and capital vs. risk (ribbon chart), for Gradient model portfolios or reference portfolios, under the baseline or any Gradient regime, with an automatic desmoothing check for private markets. Produces clean, visual Gradient images and LinkedIn, Substack and X copy. Use whenever the user asks for marginal return or marginal risk, risk contribution, risk budget, where the risk sits, a 'what if we moved X% from A to B' post, or a model portfolio post."
---

# Gradient PA · Marginal

> **Archived legacy reference — do not execute directly.** Current Portfolio Lens workflows use `SKILL.md` at the skill root, `references/lens-framework.md`, and `scripts/build_cma_mcp.py`. Legacy script names below (`build_cma.py`, `check_core_sync.py`, `pa_framework.md`) are retained for historical reference only.

Three formats on a Gradient model (or reference portfolio), each under any `scenario`:
- `marginal_map`: **ranked bars** of the implied % change in return per unit of risk from adding 1% to each class (funded pro rata); best lime, worst muted coral. Hero: the best class's implied change.
- `marginal_move`: **before/after risk bars** with only the moved class colored. Hero: implied change in volatility for the change in return.
- `capital_vs_risk`: **ribbon** from capital to implied risk with only the dominant class colored. Hero: that class, capital → implied risk.

## Spec
`format`, `portfolios: [model]` (e.g. `model_total_plan.json` or `lib:global_60_40`), optional `scenario` (any framework id), `move` (`{"from", "to", "amount"}`) for `marginal_move`, `marginal_step` / `marginal_level` for `marginal_map`, `acknowledge_sensitivity_flip` only for an explicitly two-sided post.

## Idea menu
- Next 1% (`marginal_map`): the materiality rule blocks it when class differences are tiny, as on the Total Plan (+0.8% vs −0.7% change in the ratio). Use it only where differences clear the rule.
- Total Plan, 5% Public Equity → Private Debt (example): implied −0.39 pp of volatility for −0.03 pp of return; survives the desmoothing check (−0.29 pp); state illiquidity and fees are excluded.
- Total Plan, capital vs. risk (example): Public Equity 35% of capital, an implied 58% of risk.
- Global 60/40, next 1% in Stagflation.
- Total Plan, 3% Cash → Public Equity under the current regime.

## Before you start
Read `references/pa_framework.md`: portfolio and scenario libraries, methods, real-data rules, caveats, **visual design** and writing rules. It is identical in every `gradient-pa-*` skill. Run `python3 scripts/check_core_sync.py` once per session; if shared files differ between PA skills, tell the user before rendering.

## Workflow
1. **Inputs.** Use `examples/cma_pa_q3_2026.json` and `examples/regimes_q3_2026.json` unless Gradient has published a newer CMA release (check `get_capital_market_assumptions` `view: "baseline"`, `release.version`); for a new release rebuild both (framework §6).
2. **Spec.** Copy the example spec in `examples/`, set `portfolios` and the format options, and use placeholder words.
3. **Facts.** `python3 scripts/pa_viz.py facts --spec <spec.json>` prints every computed number. Pick **one** point from these numbers only; secondary findings become their own posts.
4. **Words.** Two fields only on the image:
   - `headline` (≤90 characters, two lines): the implied result with its metric, in model-implied language ("Gradient's assumptions imply…", "Implied…"), no vague verbs and never stated as fact.
   - `takeaway` (aim for 300–380 characters, hard limit 440), in model-implied language, starting with **"Why:"**: the **root cause** of the one point, naming the specific assumptions that drive it and their values (from `facts` → `assumptions`). Do not restate the result (the mechanism: correlation, volatility, carry, regime multipliers), plus any caveat that changes the reading.
      - Page 2 highlights: `highlight_factors` (and `highlight_scenarios`, `regime_factors`) for the assumptions the takeaway names.
   The renderer computes the hero number and its caption. Every number in the words must appear in `facts` (results under the format keys, assumptions under `assumptions`).
5. **Render and inspect.** `python3 scripts/pa_viz.py render --spec <spec.json> --out <OUTPUT_DIR>/pa` (the session's outputs folder). Open all four PNGs (page 1 and the page-2 assumptions card, `…_p2.png`, in both sizes); check labels don't collide, the chart reads at a glance, and the footer is intact. If the script stops for space, shorten the takeaway or headline. If it stops on the desmoothing check, do not publish the finding (framework §4).
6. **Post copy.** Write `post_copy.md` (LinkedIn, Substack with a Method section, X). Put the mechanism, caveats, "what would change our read" and method there, not on the image. Deliver the LinkedIn PDF (`…_linkedin.pdf`, page 1 + page 2 for a document carousel), the PNGs and the copy with the session's file tool, plus a short evidence note (CMA release, regime calibration id, portfolios and weights, scenarios, any what-if or caveat).

## Files
`scripts/pa_core.py` (shared engine, libraries, scenarios, currency), `scripts/pa_viz.py` (shared visual renderer), `scripts/brand.py` (brand), `scripts/check_core_sync.py`, `scripts/build_model.py`, `scripts/build_cma.py`; `references/pa_framework.md`, `references/models_and_data.md`, `references/sleeve_factor_map.json`; `examples/` (Q3 2026 inputs, Gradient models, sample specs); `assets/fonts/` (Inter, OFL); `assets/logos/`.
