# Portfolio Lens framework

Used by `gradient-portfolio-lens`. Each post is one cell in a grid:

**portfolio × scenario × analytics × canvas**

Canvas grammar, brand and copy rules live in `canvas-spec.md`; this file covers what is computed and the gates.

| Canvas (`format`) | Chart | Question |
|---|---|---|
| `capital_vs_risk` | ribbon from capital to implied risk | Where does the risk sit? |
| `marginal_move` | before/after risk-mix bars | What does moving X% from A to B change? |
| `marginal_map` | ranked bars | Which class improves efficiency at the next 1%? |
| `head_to_head` | dumbbell by economy | What does moving from allocation A to B buy, economy by economy? |
| `scenario_stress` | ranked bars by economy | How does one portfolio change across regimes and what-ifs? |
| `equity_dial` | line of return per unit of risk vs. equity share | Where does the equity mix earn the most per unit of risk? |
| `diversifier_scorecard` | ranked bars with Δ return · Δ vol · correlation | What does a 10% sleeve of each diversifier change? |
| `currency_lens` | hedge-ratio curve | How does it look from a EUR or GBP seat? (**blocked**, §4) |

## 1. Portfolio library
**Reference portfolios** (`lib:<key>`), built from Gradient CMA factors, weights printed on the image. **Global Public
Equity** means Gradient's house global equity mix: **80% developed, 20% emerging** (factors 1 and 6). Keys:
`global_60_40`, `global_70_30`, `global_50_50`, `global_40_60`, `global_80_20` (Global Public Equity / Global Aggregate
Bonds), `global_60_40_govt` (Global Government Bonds), `global_60_30_10` (10% Cash), `dm_60_40` (developed only).

**Gradient illustrative archetypes** (`lib:<key>`): `endowment_style`, `public_pension_style`, `foundation_70_30_alts`,
`60_40_plus_alts` (50/30/20) and `all_weather_style`. Weights are in `pa_core.ARCHETYPES`. They are stylized weights
defined by Gradient, **not peer, survey or institution data**; every image prints "Gradient illustrative archetype:
stylized weights, not peer or survey data". Gradient no longer publishes peer analysis: never call an archetype "the
average" anything or compare it to peers.

**Gradient models** (policy weights only): `examples/model_total_plan.json`, `examples/model_private_markets.json`;
build others with `scripts/build_model.py`.

## 2. Scenario library
| id | Label | Kind |
|---|---|---|
| `baseline` | Baseline | Gradient ICAPM baseline |
| `regime:RECOVERY` … `regime:SYSTEMIC_STRESS` (7) | Regime name (persistence of 10 yrs) | Gradient regime overlay blended into the 10-yr view |
| `regime:current` | Current Regime (…) | The regime in `current_mapping`; **stops when its `as_of` is over 45 days old** |
| `whatif:stock_bond_corr_+0.4` | Stock–Bond Sync | What-if: equity–bond correlations set to +0.4. Not a Gradient forecast: always labeled |
| `sensitivity:private_vols_house` | Private Vols at Policy Level | Private-vol check (automatic when private markets are present) |

**Regime method** (reproduces Gradient's `grip_cma_statistics`): w = min(persistence, 10 yrs)/10; return =
μ × [(1 − w) + w × returnMult] + w × returnAdd; volatility = σ × √[(1 − w) + w × volMult²]; correlations unchanged.
Overlays must match the CMA release (`compatible_cma_release`); the renderer stops otherwise. Factors without an
overlay (for example Gold) are not regime-adjusted: say so if a post leans on them.

**Rising rates:** the CMA has no bond duration, so there is no duration shock. Tell rate stories through Late Cycle and
Stagflation. Say "rising-rate regimes", never "a 100 bp shock".

## 3. Analytics
**Gradient's CMAs are an International CAPM (ICAPM):** total expected return = strategic local cash rate + risk premium
(`excess_return_effective`). Read the cash rate from the CMA file (`usd_cash_rate`); never type it. "Return per unit of
risk" uses the risk premium.

Computed by `pa_core.py` from the MCP-built CMA file, and **cross-checked against the MCP** for the base portfolio of
every post (`mcp_check.py`): expected excess and total return, volatility from the full correlation matrix, each class's
share of risk (Euler), marginal return and risk of +1% (funded pro rata), move deltas with policy-band checks,
head-to-head deltas and return per unit of added risk, the equity-dial sweep and ratio peak, and the diversifier
scorecard (each candidate added as a sleeve, funded pro rata).

## 4. Gates (enforced by the scripts)
- **MCP source and cross-check.** The CMA file must be built by `build_cma_mcp.py` (`provenance.source:
  gradient_mcp`), and every render needs a saved MCP `portfolio_analytics` result for its base portfolio that matches
  the local engine (0.5 bp return, 0.5 bp volatility, 0.25 pp risk share).
- **Validation:** `passed`, or `passed_with_warnings` with advisory checks only.
- **Policy weights only;** never holdings, "actual" weights, fund or manager names, or Strategy Lab demo series.
- **Private-vol check:** any portfolio or candidate with private markets is rerun with Gradient's policy-channel
  private-market volatilities. If the conclusion flips, the render stops; publish only as an explicitly two-sided post
  (`acknowledge_sensitivity_flip: true`).
- **Materiality:** a ranking needs a gap of at least 0.02 in return per unit of risk for scenario and head-to-head
  claims, and 0.005 between the top two classes or diversifiers. Below that, make a directional point
  (`acknowledge_small_differences: true`). The equity dial says "effectively tied" when a portfolio is within 0.02 of the peak.
- **Persistence:** Scenario Stress reruns every regime at 2.5 years; if the weakest changes, say so (`acknowledge_persistence: true`).
- **Currency lens is blocked** until Gradient confirms `fx.expected_change_basis` and the FX inputs. The MCP's FX
  correlation matrix is close to the identity and several FX volatilities are round placeholders (EUR 5%, AUD/NOK/SEK
  12%), so no currency post until Gradient fixes them.

## 5. Caveats (re-check every release; the registry is `pa_core.UNDER_REVIEW`)
Factors under review get an amber "Under review" line on the image when a post leans on them (≥5% weight, a
highlight, or a scorecard candidate), and the scorecard leaves them out unless `include_under_review: true`:
- **Gold:** volatility is a round 12% and its correlation with developed equity (0.52) is high versus history.
- **Infrastructure:** expected return over cash (1.86%) sits below High Yield.

Also mention when relevant:
- **Stock–bond correlation ≈ 0** (developed equity vs. aggregate bonds −0.03 in the Oct 30 matrix). It drives
  "equities carry most of a 60/40's risk"; use the Stock–Bond Sync what-if as the counterpoint.
- **Private-market volatilities are not desmoothed** in the published CMA (`inverse_desmoothing_applied: false`).
  The policy-channel volatilities (PE 34.9%, RE 18.1%, Infra 15.8%, DL 16.5%) are the sensitivity case.
- **Resolved in the live build:** High Yield's correlation with developed equity is now +0.64 (the old snapshot had
  −0.05), so High Yield stories are fine again.

## 6. Inputs and refresh
See SKILL.md step 1. `examples/cma_live.json` is built from `examples/mcp/*.json` (Q3-2026-policy-v2.4, publication
57444553…, correlations as of Oct 30, 2026). Never hand-copy numbers into the CMA file.

## 7. Visual design (built into `scripts/pa_viz.py`)
**One core point per canvas.** Every image makes exactly one point that a non-technical reader can grasp in a few seconds; the chart highlights only the element that carries that point (lime for the answer, muted coral for the weakest case, grey for everything else). Secondary findings become separate posts or go in the post text. Every image has the same calm structure:
1. Header (Gradient logo, "Portfolio Lens", CMA date) and a one-line eyebrow (format · portfolios · scenario).
2. **Headline** (≤90 characters, two lines): the measured result.
3. **One hero number** with a two-line caption (computed by the renderer).
4. **One simple chart** taking most of the canvas: dumbbell (head-to-head), ranked bars by economy (scenario stress), one investor's hedge-ratio curve with unhedged / most efficient / fully hedged marked (currency lens; one home currency per post), ranked bars of the implied change in risk-adjusted return from adding 1% (next 1%), before/after risk bars with only the moved class colored (marginal move), or a ribbon with only the dominant class colored (capital vs. risk). No tables, tiles, grids or multi-series clutter.
5. **Takeaway** (aim for 300–380 characters; hard limit 440), left-aligned, starting with "Why:": the root cause of the single point, naming the driving assumptions and their values.
6. One small footer block: sources, method notes and disclaimer.
Everything else (mechanism, caveats, "what would change our read", method, proxy lists) goes in the post text. The allocation appears once: in the chart legend or labels.

Spec words: `headline`, `takeaway`. Inputs: `format`, `portfolios` (list: `lib:<key>` or a model file), `cma`, `regimes`, and format options (`scenarios`, `homes`, `scenario`, `move`, `marginal_step`, `marginal_level`, `acknowledge_sensitivity_flip`).

### Page 2: the assumptions card (`…_p2.png`, rendered automatically)
Every post has a second image in the same style showing the Gradient capital market assumptions behind page 1: **Return and risk** (expected return over cash, volatility, return per unit of risk, weights), a **second-order card** (correlations among the assets used, or the currency assumptions), and **Regime overlays** (implied return and volatility per regime, with assumed persistence) for scenario posts. Rows that drive the result are highlighted in lime via spec keys `highlight_factors` (factor ids, or for currency posts `"fx"`, `"USD"`, `"EUR"`, `"GBP"`, or an asset name), `highlight_scenarios` (regime labels) and `regime_factors` (which factor columns to show in the regime card). Highlighted factors are always shown even if small. Set `no_page2: true` only if the user asks for a single image.

**Publishing on LinkedIn:** the renderer also writes `…_linkedin.pdf` (portrait page 1 + page 2). Upload it with LinkedIn's "Add a document" option so it shows as a swipeable carousel, and give it a short document title (the headline works). Use the square PNGs for X or other channels.

## 8. Writing rules
- **Explain the root cause, not the result.** The takeaway starts with "Why:" and names the specific assumption(s) that produce the result, with their values from page 2 (for example "Gradient assumes bonds earn more per unit of risk on their own (0.38) than developed or emerging equity (0.36 and 0.35) and are nearly uncorrelated with equities (−0.06)"). Never just restate the chart or say "Gradient's assumptions" without saying which assumption and why it matters. Highlight the same assumptions on page 2.
- **Model-implied language, always.** Every figure is the output of Gradient's capital market assumptions, regime overlays and scenario analytics, not an observed fact or a forecast. Say "Gradient's assumptions imply", "the scenario analytics imply", "is expected to", "an implied 58% of risk", "on Gradient's assumptions". Never state results as facts: avoid "earns", "returns", "carries", "adds", "costs", "beats", "wins", "falls to" without "implied" or "expected". Example headline: "Gradient's assumptions imply a higher risk-adjusted return for the 60/40 in every scenario."
- **Precise headlines.** State the measured result with its metric and, where it fits, the numbers. No vague verbs (hurts, helps, wins, beats, pays) and no elliptical phrases ("a sterling one"). Example: "Implied best risk-adjusted dollar hedge: 30% for euro investors, near 100% for sterling".
- **Say things once.** The allocation appears only in the allocation strip (with the Global Public Equity mix); the subtitle names the assumptions; "not a forecast" lives in the disclaimer.
- **Lead with risk-adjusted return** (return per unit of risk). Use lowest or highest risk only as supporting detail. Headlines and the first tile should be about return per unit of risk (or return per unit of added risk for head-to-heads).
- **Say what the equity is.** Call it Global Public Equity; the allocation strip states the 80% developed / 20% emerging mix.
- **No index-provider or product brands** (for example no ACWI, MSCI, S&P 500, Bloomberg Aggregate, FTSE or tickers). Use Gradient's names: Global Public Equity, Developed Equity, Emerging Equity, Global Aggregate Bonds, Global Government Bonds, Cash.
- Headline ≤90 characters (aim for under 60): the result, plain words, Title Case for portfolio, class and regime names.
- Analysis: result with numbers → mechanism (correlation, volatility, carry, regime multipliers) → caveat → "Our read:" framed for a committee, never a recommendation.
- "Expected", "assumed", "on Gradient's assumptions". Never "will", "should", "forecast", "investors should".
- Post copy: LinkedIn (150–250 words, ends with "Gradient capital market assumptions (release). Not investment advice. GradientCIO.com"), Substack (300–500 words with a **Method** section: portfolios and weights, CMA release, scenario method, any what-if or proxy), X (≤280).
- Disclaimer (on the image, in the same small text block as the sources, and in Substack): "For informational purposes only; not investment advice. Figures are model assumptions, not forecasts, and commentary is interpretation. Past performance and model assumptions do not guarantee future results."
