---
name: "gradient-pa-head-to-head"
description: "Gradient PA · Head-to-Head: compares two allocations (for example Global 60/40 vs 70/30, a 60/40 with government bonds or cash, a Gradient model vs a sleeve model) across Gradient's economic regimes and what-if scenarios on a dumbbell chart of return per unit of risk, with the marginal difference (extra return, extra risk, return per unit of added risk) in the facts and post text. Produces clean, visual Gradient images and LinkedIn, Substack and X copy from Gradient capital market assumptions and regime overlays. Use whenever the user asks to compare two portfolios or allocations, 60/40 vs 70/30, more vs less equity, or 'what does moving from A to B buy in each economy'."
---

# Gradient PA · Head-to-Head

Two allocations, several economies: **which has the higher implied return per unit of risk, and what would moving from A to B be expected to change?**

**Chart:** a dumbbell per scenario on an implied return-per-unit-of-risk axis (lime = first portfolio, slate = second, allocations in the legend). One point: which portfolio sits to the right. **Hero:** both baseline ratios and how many scenarios the leader wins. Extra return, extra risk and return per unit of added risk per scenario are in `facts` for the takeaway and post text.

## Spec
`format: "head_to_head"`, `portfolios: [A, B]`, `scenarios` (default: baseline, five regimes, the stocks-and-bonds-in-sync what-if).

## Idea menu
- Global 60/40 vs 70/30 (sample): more equity implies a lower ratio in all seven scenarios (gap ≥ 0.02 in five); the ratio would peak near 26% equity, which the post states as context.
- Global 60/40 vs 50/50 and 40/60: how much risk-adjusted return de-risking adds or costs by regime.
- Global 60/40 vs Developed-Markets 60/40 (`dm_60_40`): what the 20% emerging share does.
- Global 60/40 vs Global 60/40 with Government Bonds (`global_60_40_govt`): the better diversifier in Systemic Stress and Stagflation.
- Global 60/30/10 with Cash (`global_60_30_10`) vs Global 60/40.
Re-run `facts` every time; never reuse numbers across releases. Write every result as model-implied (framework §8).

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
