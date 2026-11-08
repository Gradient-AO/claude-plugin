---
name: gradient-portfolio-lens
description: "Create a Portfolio Lens Quick Take from Gradient assumptions and portfolio analytics. Triggers: 'Portfolio Lens', '60/40 risk', 'marginal move', 'stress map', 'equity dial', 'diversifier scorecard'. For a committee report use gradient-portfolio-review."
metadata:
  group: "Quick Takes"
  subject: "illustrative portfolio analytics"
  output: "canvas"
  menu_order: "10"
  modules: "research"
  contracts: "quick-takes,portfolio"
  handoffs: "gradient-portfolio-review"
  delivery: files
  status: "core"
  version: "1.1.0"
  summary: "Explain illustrative portfolio risk, allocation moves, stresses and diversifiers."
---

# Portfolio Lens

Quick Takes on common portfolios that show what Gradient computes. Read **`references/canvas-spec.md`** (canvas grammar,
brand, data rules, copy patterns) and **`references/lens-framework.md`** (portfolio library, scenarios, methods, gates,
caveats) before starting. Also read
**`${CLAUDE_PLUGIN_ROOT}/shared/contracts/mcp-evidence-and-analytics.md`** before calling analytics tools.

Each run produces page 1 and the page-2 assumptions card in square (1080×1080) and portrait (1080×1350), a LinkedIn
carousel PDF, `post_copy.md`, and an evidence note for the user.

## Canvases (`format`)

| Format | Question | Portfolios | Hero |
|---|---|---|---|
| `capital_vs_risk` | Where does the risk sit? | one | largest class: capital % → implied risk % |
| `marginal_move` | What does moving X% from A to B change? | one + `move` | Δ volatility for Δ return |
| `marginal_map` | Which class improves efficiency at the margin (next 1%)? | one | best class's implied change |
| `head_to_head` | A vs. B across economies | two | ratios in the baseline, count of scenarios A leads |
| `scenario_stress` | One portfolio across regimes and what-ifs | one | baseline → weakest scenario |
| `equity_dial` | Return per unit of risk from 0% to 100% equity | one or more on the same dial | the peak equity share |
| `diversifier_scorecard` | What does a 10% sleeve of each diversifier do to a portfolio? | one | the best diversifier's implied change |
| `currency_lens` | The portfolio from a EUR or GBP investor's seat | one | **blocked** until Gradient confirms its FX inputs |

**Portfolios:** `lib:global_60_40`, `lib:global_70_30`, `lib:global_50_50`, `lib:global_40_60`, `lib:global_80_20`,
`lib:global_60_40_govt`, `lib:global_60_30_10`, `lib:dm_60_40`; archetypes `lib:endowment_style`,
`lib:public_pension_style`, `lib:foundation_70_30_alts`, `lib:60_40_plus_alts`, `lib:all_weather_style`; Gradient
models `model_total_plan.json`, `model_private_markets.json` (build others with `scripts/build_model.py`).
Archetypes are stylized weights defined by Gradient; never call one "the average" pension, endowment or foundation.

## Workflow

### 1. Refresh the inputs from the MCP (each new CMA release or publication)
Compare `get_capital_market_assumptions view=baseline` → `release.version` and `publication.publication_id` with
`examples/cma_live.json` → `release` and `provenance.publication_id`. If either differs, rebuild:
1. Call `view=baseline` with `per_page: 10`, pages 1 and 2, `fields`: `items.factor_id`, `items.name`,
   `items.excess_return_effective`, `items.volatility_effective`, `items.volatility_policy` (page 1 also `release`,
   `risk_free_rate.effective`, `publication.publication_id`). Save each result as returned.
2. Call `view=correlations` with `factor_ids` [1, 4, 5, 6, 7, 8, 9, 11, 12, 13, 14, 15, 16, 17, 18, 19] and `fields`:
   `dense_matrix`, `release`, `estimation_metadata`, `matrix_validation`, `publication`. Save it.
3. `python3 scripts/build_cma_mcp.py --baseline <p1> <p2> --correlations <corr> --carry-fx examples/cma_live.json --out examples/cma_live.json`
4. When the release changes, refresh the regime file from `view=regime` (all seven regimes,
   `slices: ["factor_adjustments"]`). Refresh `current_mapping` and its `as_of` from `get_macro_signals`
   (`grip_cma_statistics`; `regime_state` once Gradient resumes publishing it).

### 2. Pick the canvas and the portfolio
Choose one point a CIO would find useful. Check `quicktakes.csv` (canvas-spec §9) so the portfolio × format does not repeat
within a quarter. Copy the closest spec from `examples/` (`post_*.json`).

### 3. Collect server analytics evidence (required for every post)
```
python3 scripts/pa_viz.py mcp-weights --spec <spec.json>
```
The command prints the server calls required by the selected format. Save every result and list it in the spec's
`mcp_evidence` manifest. Use `portfolio_analytics` for each point allocation, `allocation_frontier` for frontier
formats, and `allocation_regimes` for governed regime rows. These are inline-only ad hoc calls: always pass `weights`
and never pass `portfolio_id` or rely on a loaded portfolio.

Displayed return, volatility, Sharpe, variance and risk-contribution values come from those saved server payloads.
`pa_core.py` recomputes them only as a regression check. The render stops on a missing payload, stale release, different
weights, failed server validation, or a regression difference beyond tolerance.

Do not substitute the efficient frontier for the old next-1% or fixed-equity-dial perturbation. Publish
`marginal_map` or `equity_dial` only when the evidence manifest contains the documented server variants needed by that
chart. Unsupported local what-if scenarios stay explicitly labeled local and separate from governed regime rows.

### 4. Facts, then words
```
python3 scripts/pa_viz.py facts --spec <spec.json>
```
Write two fields only, from these numbers:
- `headline` (≤90 characters): the implied result with its metric, in model-implied language ("Gradient's assumptions imply…").
- `takeaway` (≤440, aim 300–380), starting **"Why:"**: the root cause, naming the specific assumptions and their values.
  Set `highlight_factors` (and `highlight_scenarios`, `regime_factors`) so page 2 highlights them.
Also write down the plain-English question a CIO would type into Claude; it goes in the post text.

### 5. Render and inspect
```
python3 scripts/pa_viz.py render --spec <spec.json> --out <OUTPUT_DIR>/lens
```
Open all four PNGs. Check for overlaps, clipped labels and a squashed chart. The renderer stops when a claim would not
survive review; the stop message says what to change:
- **Materiality** (`marginal_map`, `diversifier_scorecard`): differences too small to rank. Make a directional point
  with `acknowledge_small_differences: true`, or use a larger step.
- **Persistence** (`scenario_stress`): the weakest scenario changes at equal assumed duration. Say so
  (`acknowledge_persistence: true`) or make a different point.
- **Private-vol check** (any private markets): the conclusion flips at Gradient's policy-channel private-market
  volatilities. Publish only as an explicitly two-sided post (`acknowledge_sensitivity_flip: true`), as in
  `post_diversifiers_60_40.json`.
- A **current regime** older than 45 days, a **regime/CMA release mismatch**, a **CMA file not built from MCP
  payloads**, or **no MCP cross-check**.

### 6. Post copy and evidence note
Write `post_copy.md` per canvas-spec §8. The "How we made this" line names the capability, e.g. *"Claude pulled
Gradient's Q3 2026 capital market assumptions and had Gradient's server compute the portfolio's risk contributions;
every number on the image comes from that output."* The Substack **Method** section lists the portfolio weights (and
the archetype label), proxies, scenario method, CMA release, caveats and the MCP payload digest. Deliver the PNGs, the
LinkedIn PDF and `post_copy.md`, then the evidence note: CMA release and publication ID, the MCP cross-check digest and
diffs, every gate result, and the source of every claim.

## Files
- `scripts/pa_core.py`: regression engine (portfolio library, scenarios, gates and caveats); never the publication
  source when server analytics are available.
- `scripts/pa_viz.py`: server-payload facts, regression gates and renderer for every canvas, plus page 2 and the LinkedIn PDF.
- `scripts/mcp_check.py`: prints the spec-driven MCP evidence recipe and verifies every saved result.
- `scripts/build_cma_mcp.py`: builds the CMA file from saved MCP payloads. `scripts/build_model.py`: model files.
- `scripts/brand.py`, `assets/`, `references/canvas-spec.md`: synced from the plugin's shared Quick Take kit. Do not edit here.
- `references/lens-framework.md`; `references/legacy/` (the retired skills' instructions and idea menus, for reference).
- `examples/`: `cma_live.json` (built from MCP payloads in `examples/mcp/`), regimes, models and one spec per canvas.
  `cma_pa_q3_2026.json` is the retired hand-built snapshot, kept only to show the drift; renders refuse it.
