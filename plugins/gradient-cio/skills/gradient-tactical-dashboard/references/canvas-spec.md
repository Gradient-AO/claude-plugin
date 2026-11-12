# Quick Takes: the canvas spec

A **Quick Take** is a one-page, shareable canvas built from Gradient data: one insight, one chart, the reasoning behind
it, and the sources, ready for LinkedIn, Substack, X, an email or a committee pre-read. Five skills in the GradientCIO
plugin make them; this spec defines every canvas. Source of truth: `quicktake-shared/canvas-spec.md`; each skill carries
a synced copy at `references/canvas-spec.md`. Edit only the shared file, then run `python3 tools/sync_quicktake_shared.py`.

## 1. What a Quick Take is for

A Quick Take answers one question an investment committee would ask, with Gradient's numbers doing the work: what
Gradient's assumptions imply for a portfolio, which market move was unusual, where risk pressure is coming from. The
reader should come away understanding the result **and** how it was produced, so they can ask the same question about
their own portfolio.

Test every draft: *is the analysis doing the talking?* Let the data be the subject of the sentence ("Gradient's
assumptions imply…", "the scan ranked…", "one question in Claude pulled…"), never a personal market view.

## 2. The five Quick Takes

| Quick Take | Skill | Question it answers | Good for | Main Gradient capability shown |
|---|---|---|---|---|
| **Portfolio Lens** | `gradient-portfolio-lens` | What do Gradient's assumptions imply for a common portfolio? | Allocation discussions, education, committee pre-reads | CMA `portfolio_analytics` (server-computed return, risk, Euler risk contribution), regime overlays, correlations |
| **Signal Spotlight** | `gradient-signal-spotlight` | Which spread moved unusually, and why? | A weekly market note | `get_macro_signals` relative returns |
| **Risk Pulse** | `gradient-risk-pulse` | Where is market risk pressure coming from? | A weekly risk note (gated when GRIP is saturated) | `get_macro_signals` GRIP |
| **Tactical Dashboard** | `gradient-tactical-dashboard` | Where do momentum, signals and 10-year assumptions disagree? | A monthly scorecard | Relative returns + CMA + GRIP (+ regime when published) |
| **Ask Gradient** | `gradient-ask-gradient` | One real question, answered live with Gradient data | Anything that fits one question | Rotates across the platform (see that skill's topic table) |

If you publish regularly: don't repeat a portfolio × canvas or a pair within a quarter, rotate Spotlight themes
(regions → sectors → styles → cross-asset), and keep a log (section 9).

## 3. Sizes and deliverables

- **Square** 1080 × 1080 (LinkedIn, X) and **portrait** 1080 × 1350 (LinkedIn feed). Always render both.
- **Portfolio Lens** also renders **page 2, the assumptions card** (`…_p2.png`) in both sizes and a **LinkedIn document
  carousel** PDF (portrait page 1 + page 2).
- `post_copy.md` with LinkedIn, Substack and X copy, saved next to the images.
- An **evidence note** for the user (never posted): every input's validation status, as-of date, methodology
  reference and the first 12 characters of each payload digest, plus the source of every claim.

## 4. The canvas grammar (top to bottom, every post)

| Zone | Content | Limits |
|---|---|---|
| 1 · Lockup bar | Gradient logo (left); series name · as-of date (right); thin rule | Logo from official files only |
| 2 · Eyebrow | Series label · subject (pair, portfolio or question topic) · scenario if not baseline | One line, set by the renderer |
| 3 · Headline | One plain-English claim, readable without the question | ≤90 characters (aim 45–66) |
| 4 · Subtitle (Signals) | How to read the chart | One line |
| 5 · Hero | One number + two captions (Lens), stat panel or ≤3 tiles (Signals) | Computed by the renderer, never typed |
| 6 · Chart | **One** simple chart that carries the result | Must keep the minimum height the renderer enforces |
| 7 · Analysis | Lens: "Why:" takeaway naming the assumptions that drive the result. Signals: "Analysis" with the hedged driver | Lens ≤440 (aim 300–380); Signals ≤700 portrait, ~300–380 square |
| 8 · What would change our read | One observable condition, never a prediction | ≤200; portrait always, square when space allows |
| 9 · Caveat lines (automatic) | Private-vol check result; "Under review" assumptions | Drawn by the renderer when they apply |
| 10 · Footer | Source line (datasets, release, dates), MCP cross-check digest (Lens), "Built in Claude with Gradient data", the disclaimer, GradientCIO.com | Never remove |

Overflow order when a render stops for space: trim the watch line → the analysis → the headline. Never shrink the chart below its minimum.

**Page 2 (Lens only):** the Gradient capital market assumptions behind page 1: return and risk per asset (risk premium,
total expected return, volatility, premium per unit of risk, weight), the correlations or regime overlays that drive the
result, and highlighted rows for the assumptions the takeaway names.

## 5. Brand system (constants in `quicktake-shared/brand.py`)

- Colors: background `#0D1117`, panel `#161C24`, text `#F2F5F7` / `#A7B1BC`, fine print `#6E7A87`, grid `#242C36`.
  **Gradient lime `#C6F432` is the only highlight color**; coral `#FF6B5E` for down moves. Lens charts use the muted
  palette in `pa_viz.py` so lime stays the single highlight.
- Font: Inter (bundled, SIL OFL), DejaVu Sans fallback. Typographic punctuation in display text (’ “ ” −).
- **Two layout profiles, one kit:** `signals` (larger lockup, footer with GradientCIO.com and the built-with line) and
  `lens` (compact lockup, one small footer block so the chart owns the canvas). Same tokens, disclaimer and logos.
- **One disclaimer** (`DISCLAIMER`): *For informational purposes only; not investment advice. Figures are model
  assumptions, not forecasts, and commentary is interpretation. Past performance and model assumptions do not guarantee
  future results.* Use it at the end of every Substack post; "Not investment advice." in LinkedIn and X copy.
- **Title Case** for every pair, asset, factor, sleeve, pillar and model name ("Growth vs. Value", "Public Equity",
  "Rates, Curve & Policy"); acronyms in capitals (US, EM, DM, UK, FX, CMA); "vs." lowercase with a period. Headlines
  and sentences otherwise in sentence case.

### Logos and co-branding
- Put the official files in `quicktake-shared/logos/` (light versions for a dark background): `gradient.svg|png` and, only once
  approved, `claude.svg|png`. Sync copies them to every skill. **Missing files fall back to a text wordmark: install the
  official Gradient logo before the next publishing cycle.**
- **Default brand mode is `gradient`** (Gradient logo alone, plus the factual "Built in Claude with Gradient data" line).
  `cobrand` adds the Claude logo and requires Anthropic's prior approval under its trademark guidelines; Gradient owns
  the decision to publish it. Never draw, trace, recolor or approximate either logo.

## 6. Data rules (all series; the renderers enforce most of them)

- **The MCP is the source of every number.** Lens builds its CMA file from MCP payloads (`build_cma_mcp.py`) and checks
  every post's base portfolio against `get_capital_market_assumptions view=portfolio_analytics` (`mcp_check.py`); a
  mismatch stops the render. Signals renderers read saved MCP payloads directly. Every number in copy must appear in the
  `facts` output, a validated Gradient payload or a cited source.
- **Validation:** `passed`, or `passed_with_warnings` where every failed check is advisory (today's CMA quality
  receipt). Anything else stops the post.
- **Freshness:** Signals data more than 3 business days old stops the render unless the user accepts dated data (then
  say the date). Lens `regime:current` stops when the current-regime mapping is over 45 days old.
- **Real data only:** policy weights, Gradient CMAs and Gradient-calculated signals. Never holdings, "actual" weights,
  fund or manager names, client data, or Strategy Lab demo series (synthetic).
- **Portfolios:** reference mixes (`lib:global_60_40` …) and **Gradient illustrative archetypes** (`lib:endowment_style`
  …) print their weights and the label "Gradient illustrative archetype: stylized weights, not peer or survey data".
  Gradient no longer publishes peer analysis: **never** describe an archetype as "the average pension/endowment" or
  compare to peers.
- **Third-party data:** never show numbers from licensed third-party CMA consensus outputs (including J.P. Morgan,
  BlackRock and others). Gradient-calculated data may be published under Gradient's brand.
- **Assumptions, not forecasts:** "Gradient's assumptions imply…", "assumed", "expected". No "will", no targets, no
  recommendations, no "investors should", no timing. Causes are hypotheses backed by dated evidence, in hedged language.
- **Honest about ordinary results:** if a move or difference is routine or small, say so. The materiality and
  persistence gates exist to stop over-claiming.

## 7. Narrative voice

- Platform as subject: "Gradient's scan flagged…", "the assumptions imply…", "the data shows…".
- Show the work: name the data, the window, the release and the as-of date. Methodology is a feature, not fine print.
- One point per post. Secondary findings become their own posts.

## 8. Post copy patterns

**"How we made this" (post text only, never on the image).** Quote the real plain-English question a CIO would type
into Claude, then say in one or two sentences what Claude did and **name the capability shown**, e.g. *"Claude pulled
Gradient's Q3 2026 capital market assumptions and had Gradient's server compute the portfolio's risk contribution;
every number on the image comes straight from that output."* Never use tool names; never a question asking for a
recommendation.

- **LinkedIn (150–250 words):** hook → what the platform found → why (the mechanism, with numbers) → "How we made this:"
  → one question inviting comments → 2–4 hashtags. Last line: `Data: Gradient <dataset>, as of <date>. Not investment
  advice. GradientCIO.com`
- **Substack (250–500 words):** title, image(s), "How to read this", the analysis, "What would change our read", and a
  **Method** section (portfolio weights, proxies, scenario method, release, caveats, MCP cross-check digest). Close with
  the disclaimer and GradientCIO.com.
- **X (≤280 characters):** finding + one-line driver + "Made in Claude with Gradient data." + "Not investment advice." +
  GradientCIO.com.

## 9. Publishing log (optional)

If you publish Quick Takes regularly, append one row per published canvas to a `quicktakes.csv` in your workspace:
`date,series,format_or_pair,portfolio,scenario,capabilities_shown,payload_digest_12,url`. Check it before choosing the
next angle so nothing repeats within a quarter.
