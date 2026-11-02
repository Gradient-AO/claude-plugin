# Templates, idea menu and copy

## The three templates
Every image shows: Gradient lockup, model + template eyebrow, headline, the mandatory model note, three computed tiles, the main chart, **the model's full policy allocation for context**, the analysis, an optional "what would change our read" line, sources and disclaimer.

| Template | Main chart | Tiles | Best for |
|---|---|---|---|
| `capital_vs_risk` | Each asset class's share of capital beside its share of risk | Expected return (excess + total), expected volatility with return per unit of risk, the largest class's risk share | "Where does the risk really sit?" A strong opener for a new model. |
| `marginal_move` | Share of risk before and after, with each class's capital change underneath | Change in expected return, change in volatility, return per unit of risk after vs. before | "What does moving X% from A to B do?" The weekly workhorse. |
| `marginal_map` | For each class (or sleeve): marginal return and marginal risk of adding 1%, funded pro rata from the rest, and the change in return per unit of risk | Portfolio return per unit of risk, the most and least efficient next 1% | "Where does the next dollar earn its risk?" The purest marginal-analytics post. |
| `model_compare` | Expected return vs. volatility for the model, other models and a reference 60/40 (60% DM equity, 40% global aggregate bonds, same assumptions) | The model's return and volatility, the best return per unit of risk, number of models | "How does the model compare with a plain 60/40?" |

**Marginal return and marginal risk** (in `facts` for every template, under `marginal`): for each class or sleeve, the exact change in expected excess return and in volatility from adding `marginal_step` (default 1% of the portfolio) funded pro rata from everything else, the change in return per unit of risk, and the analytic marginal contribution to risk (dσ/dw). Set `marginal_level: "sleeve"` for sleeve-level rows. Use these numbers to explain *why* a move works: a move from A to B helps when B's marginal return per unit of marginal risk beats A's.

**Desmoothing check** (in `facts` under `sensitivity`, printed on every image): the same results with private-market volatilities at Gradient's house level. See `models_and_data.md`.

A move can name a **sleeve** ("Private Debt") or a whole **class** ("Public Equity", moved pro rata across its sleeves). Moves are percentages of the total portfolio. The engine checks every class against its policy band after the move; never publish a move that breaches a band without saying so.

## Idea menu (pre-tested on the Total Plan, Q3 2026 assumptions)
Re-run `facts` before using any of these; numbers change with each CMA release.

| Move | Result (Δ return, Δ vol, return per unit of risk) | The story |
|---|---|---|
| 5% Public Equity → Private Debt | −0.03 pp, −0.39 pp, 0.51 → 0.53 (house vols: −0.29 pp, 0.41 → 0.42) | Risk falls far more than return (sample post). Survives the desmoothing check, smaller. |
| Next 1% to each class (`marginal_map`) | Published: Fixed Income and Alternatives improve efficiency, Public Equity hurts it most. House vols: only Fixed Income improves it | Two-sided post (sample): only Fixed Income helps under both views. |
| 5% Public Equity → Fixed Income | −0.17 pp, −0.66 pp, 0.51 → 0.53 | The classic de-risk, and what it costs in return. Depends on near-zero bond–equity correlation: say so. |
| 5% Public Equity → Real Assets | −0.09 pp, −0.32 pp, 0.51 → 0.52 | Real assets as a partial equity substitute. |
| 3% Government Bonds → Private Equity Buyout | +0.22 pp, +0.50 pp, 0.51 → 0.51 | Reaching for return: more return, proportionally more risk. |
| 3% Cash → Public Equity | +0.17 pp, +0.43 pp, 0.51 → 0.51 | The cost of a cash buffer; equity risk share rises to 60%. |
| 5% US Large Cap → International Developed | +0.06 pp, +0.14 pp, ~unchanged | Regional diversification barely changes the risk picture: one global equity factor dominates. |
| 3% US Large Cap → Emerging Markets | +0.09 pp, +0.15 pp, ~unchanged | Same lesson; EM adds return and risk in proportion. |
| 1.5% Commodities → Government Bonds | +0.02 pp, −0.15 pp, 0.51 → 0.52 | On these assumptions commodities cost risk without paying for it. |
| 5% Fixed Income → Alternatives | +0.23 pp, +0.56 pp, 0.51 → 0.50 | The endowment-style shift: more return, slightly worse efficiency. |
| 3% Real Estate Core → Infrastructure | −0.11 pp, −0.04 pp, 0.51 → 0.50 | A swap that looks neutral but loses return. |

Re-test every private-markets move with the desmoothing check before using it; several in this table will shrink or flip. Avoid moves into or out of High Yield or Emerging Market Debt until the CMA caveat in `models_and_data.md` is resolved.

Rotate: Capital vs. Risk once per model, then marginal moves, with a model comparison every month or so. Sleeve models (Global Public Equity, Fixed Income, Private Markets, Real Assets, Marketable Alternatives) give a fresh capital-vs-risk post each, once built.

## Writing the words
- **Headline (≤90, aim for under 60):** the result in plain words, with Title Case for asset classes and sleeves. "Shifting 5% to Private Debt cuts risk far more than return." Never a recommendation ("Investors should…").
- **Analysis (`explain`, ≤700; `explain_square`, about 300–380):** (1) the result with the before → after numbers from `facts`, (2) the mechanism: concentration, correlation, volatility, (3) any policy-band or assumption point, (4) "Our read:" framed as a conversation for a committee, not a trade.
- **Watch line (≤200):** the assumption that would change the result, as a condition.
- **Every number** in the headline, analysis and post copy must appear in the `facts` output, rounded as shown: two decimals for returns and volatility, two for return per unit of risk, whole percentages for shares of capital and risk.
- Words: "expected", "assumed", "on Gradient's assumptions". Never "will return", "should", "forecast". Use the real minus sign (−) and typographic apostrophes.

## Post copy
**LinkedIn (150–250 words):** hook with the result → the before/after numbers → why (concentration or correlation) → the caveat → one question for readers ("Where does your plan's risk actually sit?") → 2–4 hashtags → "Gradient model portfolio, policy weights; Gradient capital market assumptions (Q3 2026). Not investment advice. GradientCIO.com"

**Substack (300–500 words):** title, image, "How to read this", the result and mechanism, the full model allocation in a sentence, the policy-band check, what would change the read, and a **Method** section: model and policy weights, CMA release and basis (10-year arithmetic excess return over cash, USD, unhedged), the formulas in plain words (volatility from the full correlation matrix; risk share = each sleeve's contribution to total volatility), and **the full proxy list from `facts`**. End with the disclaimer and GradientCIO.com.

**X (≤280):** the result + the key numbers + "Gradient model portfolio, Gradient assumptions. Not investment advice." + GradientCIO.com.

Disclaimer (on every image and Substack post): "For informational purposes only. Commentary is interpretation, not investment advice. Past performance and model assumptions do not guarantee future results."
