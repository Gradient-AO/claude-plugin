---
name: "gradient-pa-scenario-stress"
description: "Gradient PA · Scenario Stress: plots one portfolio (a 60/40, 70/30 or any reference portfolio, or a Gradient model) across Gradient's economic regimes (Recovery, Reflation, Disinflationary Growth, Late Cycle, Stagflation, Contraction, Systemic Stress, the current regime) and what-ifs on a risk–return map with equal-efficiency guide lines. Produces clean, visual Gradient images and LinkedIn, Substack and X copy. Use whenever the user asks how a portfolio holds up in different economies, recession, stagflation, rising-rate regimes or a correlation shock, or for a scenario or stress-test post."
---

# Gradient PA · Scenario Stress

> **Archived legacy reference — do not execute directly.** Current Portfolio Lens workflows use `SKILL.md` at the skill root, `references/lens-framework.md`, and `scripts/build_cma_mcp.py`. Legacy script names below (`build_cma.py`, `check_core_sync.py`, `pa_framework.md`) are retained for historical reference only.

One portfolio, every economy. **Chart:** ranked bars of implied return per unit of risk by economy; baseline lime (with a dashed reference line), weakest regime muted coral, the rest grey. **Hero:** baseline ratio → weakest regime's ratio. One point: how much the weakest 10-year scenarios cut the implied ratio. Scenarios within 0.02 of the weakest are highlighted as tied, and a persistence check stops the render if the ranking only reflects assumed duration (framework §4b).

## Spec
`format: "scenario_stress"`, `portfolios: [P]`, `scenarios` (up to nine). Risk shares by class are in `facts` (use them in the post text).

## Rising rates
There is no duration-based rate shock (Gradient's data has no duration). Use Late Cycle and Stagflation and call them "rising-rate regimes".

## Idea menu
- Global 60/40 (sample): Stagflation and Systemic Stress are tied as weakest (0.27 and 0.28, within the materiality gap) and the ranking flips at equal persistence, so the post makes the robust point: both cut the implied ratio by about 40%.
- Global 80/20 or 70/30 through the same regimes.
- Global 60/40 with Government Bonds: does the Systemic Stress point move?
- The Gradient Total Plan model across regimes (desmoothing check applies).

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
