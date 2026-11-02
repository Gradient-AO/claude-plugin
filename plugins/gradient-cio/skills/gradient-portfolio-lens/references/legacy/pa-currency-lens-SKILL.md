---
name: "gradient-pa-currency-lens"
description: "Gradient PA · Currency Lens: shows how a portfolio such as a global 60/40 or 70/30 looks to USD, EUR and GBP investors as hedge-ratio curves (return per unit of risk from 0% to 100% of the dollar exposure hedged), using Gradient's USD Index factor and Gradient cash rates by currency. Produces clean, visual Gradient images and LinkedIn, Substack and X copy. Use whenever the user asks about currency risk, FX hedging, hedge ratios, a euro or sterling investor's view of a 60/40, or the hidden currency bet in a global portfolio."
---

# Gradient PA · Currency Lens

> **Blocked pending data confirmation.** The renderer refuses to run until the CMA file records `fx.expected_change_basis` (spot change vs currency excess return, confirmed by Gradient) and `fx.usd_share` (USD-denominated share of each factor). Peer-review tests showed the best hedge ratio moves from 30% to 0% or ~100% depending on these two inputs (framework §4b). The samples are withheld.

**Chart:** one investor's curve: implied return per unit of risk against the share of the dollar exposure hedged (0–100% in 5% steps), with unhedged, most efficient and fully hedged marked. **One home currency per post** (`focus_home`); make the sterling or euro view its own post. **Hero:** the implied most efficient hedge ratio.

## Spec
`format: "currency_lens"`, `portfolios: [P]`, `homes` (include the focus currency), `focus_home` (`EUR` or `GBP`).

## Limits (state them in the Method section)
- Supported portfolios: Developed Equity, Emerging Equity, Global Aggregate Bonds, Global Government Bonds, Cash (all Global Public Equity reference portfolios qualify).
- Dollar driver: Gradient's USD Index factor for every non-USD investor; avoid JPY (weak proxy).
- Gradient's API does not yet add currency risk for non-USD base currencies; this is the disclosed workaround.

## Idea menu
- Global 60/40, euro investor (sample): the implied ratio peaks at 0.52 at 30% hedged (0.45 fully hedged).
- Global 60/40, sterling investor (sample): the implied ratio rises from 0.36 unhedged to 0.45 near fully hedged.
- Global 70/30 vs 60/40 from a euro seat: does more equity move the best hedge ratio?
- Developed-Markets 60/40 vs Global 60/40: the emerging share's stronger negative dollar correlation.

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
