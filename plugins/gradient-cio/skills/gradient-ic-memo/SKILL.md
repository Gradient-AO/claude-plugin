---
name: gradient-ic-memo
description: Write a deterministic, fully sourced investment committee (IC) memo for a portfolio, total fund, allocation change, rebalance, or manager hire/fire, using GradientCIO Portfolio Analytics, CMAs, liquidity and manager-diligence evidence, with optional Strategy Lab analysis of separately selected return series, plus the gradient-gips-* skills. Delivers a branded PDF memo in the Gradient house style. Use this skill whenever the user asks for an IC memo, investment committee memo, board memo, investment memo, committee paper, allocation recommendation, rebalance proposal, a portfolio review that ends in a decision or vote, IPS compliance review, or a client or trustee memo about a portfolio — even if they don't say "IC memo". Also use it when another skill (such as gradient-gips-manager-diligence) hands over a section "for the investment memo". For a periodic performance report with no decision requested, use gradient-portfolio-review instead.
metadata:
  version: "0.1.0"
---

# Gradient IC Memo

Produce an investment committee memo that is **deterministic** (same inputs → same structure, same tables, same
wording rules), **fully attributed** (every number traces to a Gradient tool result, a user document, or a
documented calculation), and **decision-ready** (the recommendation and the vote requested come first).

The memo is written by Claude from structured data. The GradientCIO MCP supplies the data; this skill supplies
the structure and the rules. Never fill a number from memory or general knowledge.

## Files in this skill

| File | Read when |
|---|---|
| `references/memo-template.md` | Always — the exact memo structure. Follow it verbatim. |
| `references/data-map.md` | Always — which Gradient tool feeds each section, and the fallback when data is missing. |
| `references/module-scope.md` | Always — hard boundary between saved-portfolio evidence and Strategy Lab return-series analysis. |
| `references/chart-data.md` | Always — dashboard chart discovery, basis rules and generic report block. |
| `references/ips-schema.md` | When an IPS is supplied or needed — how to capture IPS constraints as structured input. |
| `references/calculations.md` | Before drafting figures — display formats and the server-owned metric methods to preserve. |
| `references/writing-standards.md` | Before drafting prose — IC memo best practices and banned phrasing. |
| `scripts/validate_memo.py` | After drafting — confirms every section is present, in order, with no unresolved placeholders. |
| `assets/example-memo.md` | When unsure how a section should look — a complete worked example that passes validation. |
| `references/report-style.md` | Before rendering — the shared Gradient report style, `meta` fields and delivery rules. |
| `scripts/gradient_report.py` | Renders the validated markdown memo into the branded PDF. Run it; never restyle. |

## Workflow

### Step 1 — Scope the memo (ask at most one question)

Determine, from the request and conversation:

1. **Memo type** — one of: `Portfolio Review`, `Allocation Change`, `Rebalance`, `Manager Hire`,
   `Manager Termination`, `New Commitment`. The type changes only Section 1's decision wording and which
   optional rows in Section 13 apply; every section still appears.
2. **Subject** — portfolio (or total fund) and, if relevant, the manager or fund.
3. **Audience** — IC / board / trustees / client. Audience changes tone only, never structure.
4. **IPS** — attached document, pasted text, or a known IPS in the conversation. If none exists, continue and
   mark every IPS row `Not assessed — IPS not provided` (do not invent limits).
5. **As-of date** — default: the latest common date across the data returned. State it in the header.

If the portfolio itself is ambiguous, ask one question. Otherwise proceed and state assumptions in the header.

### Step 2 — Gather data from GradientCIO

Follow `references/data-map.md` section by section. Key rules:

- Load deferred Gradient tools with `tool_search` before calling them; use the parameter names from the
  loaded schema, never guessed ones.
- If the user has more than one organization, confirm which before calling org-scoped tools. Call
  `list_assumption_sets` and state the organization and selected assumption set in the memo header.
- Read `references/module-scope.md` before selecting tools. Portfolio questions use Portfolio
  Analytics. Strategy Lab is optional and uses a `build_strategy_lab_session` result built from separately
  selected `return_series_ids`. Pass the returned `strategy_lab_session` unchanged to the compute tool.
  Never pass a Portfolio Analytics `portfolio_id` to a Strategy Lab tool.
- Use `envelope: "compact"` and optional `fields` only on research-read tools whose loaded schema offers
  them. Do not pass either parameter to any `run_strategy_lab_*` tool.
- Use `get_chart_data` after portfolio selection: check availability, then request one relevant pack at a time.
  Portfolio expected-statistics and commitments packs are the primary forward-looking evidence for the saved
  portfolio. Preserve `basis` and `context.fingerprint`, skip unavailable charts with their reason, and never
  compare different bases as though they were the same scenario.
- For every result, record a **source row**: tool, key parameters, `provenance.as_of`,
  `provenance.data_scope.label`, `validation.status`, and `payload_digest` if present. These rows become the
  Appendix A source table and the `[S#]` tags in the text.
- **Illustrative data:** if any `data_scope.kind` is `illustrative`, the memo header must carry the
  illustrative banner from the template, and no sentence may describe that data as the user's holdings.
- **Validation:** a `validation.status` of `failed` with a blocking check means the value is not used; record
  the section as `Not available — validation failed (<check id>)`. Advisory failures may be used with a
  footnote.
- A tool error, entitlement block, or empty result is never silently skipped. It becomes a
  `Not available — <reason>` line in that section and an item in Section 15 (Open items).

### Step 3 — Run the GIPS workflow

The memo always contains Section 11, *Performance Integrity & GIPS*.

- **Total fund / portfolio performance reported to the committee** → use the **gradient-gips-asset-owner-review** skill
  on the performance report if one is available.
- **Each manager in Section 10 with ≥ 5% of portfolio exposure, and any manager being hired** → use the
  **gradient-gips-manager-diligence** skill.
- Paste each returned memo section into Section 11 unchanged, ordered by exposure (descending). Carry every
  High or Medium GIPS finding into Section 14 (Risks) and every follow-up into Section 15.
- If the gradient-gips-* skills are not installed, write `Not assessed — Gradient GIPS skills unavailable`
  and add the GIPS review to Section 15.

### Step 4 — Use governed server metrics

Call `check_portfolio_policy` for allocation bands, return objective, risk limits, liquidity and concentration.
Prefer `get_portfolio_attribution` for realized Brinson-Fachler effects and symmetric-Carino linking. Local
Brinson is the attribution fallback only when complete, same-period portfolio weights, benchmark weights,
portfolio segment returns, and benchmark segment returns are available from saved evidence. Label it
`Local Brinson fallback`, cite every input, and do not claim server validation or symmetric-Carino linking.
Use `get_portfolio_historical_returns` for portfolio, benchmark-relative and risk metrics. Preserve each
call's `fields` projection (`portfolio`, `filters`, `coverage`, `display` and only the requested result
sections) and each tool's methodology, formula version, basis, period, currency, coverage and missing
reasons. State partial coverage as a report gap. For `no_subject_returns`, state that the selected portfolio
has no subject return history and do not substitute benchmark, commitment or Strategy Lab returns. Other
governed results remain unavailable when their server method is unavailable.
When policy risk rows are `not_assessed`, historical-return risk metrics remain separate observations: do not
compare them with persisted thresholds or infer compliance unless `check_portfolio_policy` returns the status.
When risk rows are assessed, preserve `risk_limits.observation_basis` and the returned magnitude comparison
rule so the report states the governed horizon, effective date, frequency, return basis and currency.

Strategy Lab relative return applies only to selected lab return series and does not provide saved-portfolio
Brinson decomposition.

### Step 5 — Draft the memo

Write the memo exactly as `references/memo-template.md` specifies, applying `references/writing-standards.md`.
Determinism rules (summary — the template is authoritative):

1. All 16 sections plus the appendices, in order, with the exact headings. Never add, remove, rename or reorder.
2. Every table uses the template's columns, in order, with the template's sort rule.
3. Missing data → `Not available — <reason>` in place of the value; the row stays.
4. Number formats follow `references/calculations.md` (percentages 1 dp, active weights and spreads in bps,
   currency in millions with 1 dp, ISO dates).
5. Every number in the text or a table carries an `[S#]` tag for the Gradient result or user document that
   supplied it. Scaling and rounding for display are allowed; deriving report values locally is not.
6. Status words are only those defined in the template (for example `Compliant`, `Watch`, `Breach`,
   `Not assessed`). No synonyms.

### Step 6 — Validate, render and deliver

1. Save the draft as markdown and run `python scripts/validate_memo.py <file.md>`. Fix every error it reports
   and re-run until it passes.
2. Write `meta.json` for the cover and executive band (field reference: `references/report-style.md`):

   ```json
   {"eyebrow": "Investment Committee Memo", "header_label": "Investment Committee Memo",
    "title": "<Memo type>: <Portfolio>", "subtitle": "<Organization> · Prepared for <audience> · Meeting <date>",
    "running_head": "IC Memo · <short subject>", "data_as_of": "<as-of date>",
    "confidentiality": "Confidential — prepared for <organization> <audience> use",
    "cover_facts": [["Memo type","…"],["Meeting date","…"],["Data as of","…"],["Base currency","…"],["Assumption set","…"],["Status","Draft"]],
    "signal_title": "IPS status",
    "signal": {"level": "compliant|watch|breach|not_assessed", "label": "<e.g. 3 breaches · 2 watch>"},
    "executive": {"label": "Recommendation", "bottom_line": "<Section 1 recommendation and decision requested, with tags>"}}
   ```

   Signal level: `breach` if any IPS row is Breach; else `watch` if any is Watch; else `compliant`;
   `not_assessed` when no IPS was provided. If any data is illustrative, say so in `confidentiality`.
3. Render: `python scripts/gradient_report.py --md <file.md> --meta meta.json "<Portfolio> - IC Memo.pdf"`.
   The markdown headings become the numbered sections, status words in status columns become chips, and
   appendices start on a new page. Check every page (`pdftoppm -r 60 -png`) and fix layout before delivering.
   When including chart-pack output, build the equivalent JSON sections with the validated section markdown
   in `markdown` blocks and each returned chart item unchanged in a `{"type":"chart","chart":<item>}` block,
   then use JSON block mode. Do not hand-map chart IDs or rows.
4. Deliver the PDF (save to `/mnt/user-data/outputs/`, and to the connected folder if there is one). Offer an
   editable Claude Doc copy built from the same markdown when the committee secretary needs to edit it.
5. In the reply, give a three-line summary (recommendation, IPS status, number of open items) and the
   document. Do not repeat the memo in chat.

### Step 7 — Save the scenario (only when the user asks)

For an Allocation Change or Rebalance memo, offer to save a proposed scenario only when Section 13 used a
real Strategy Lab return-series basket or matching active lab session. Use `save_strategy_lab_scenario`
(`domain` `simulation` or `relative`, `name` "<subject> - <memo type> <meeting date>", and
the lab `form` and basket used in Section 13). Never convert a saved portfolio ID into a Strategy Lab
scenario. Call with `dry_run: true` first, show the preview, then repeat with `dry_run: false` and
`confirmation_receipt_id` set to the preview receipt only after the user confirms. Unavailable on
illustrative access: say so instead.

## Related skills

- A periodic performance and allocation report with no decision requested → `gradient-portfolio-review`.
- Choosing between candidate managers before a Manager Hire memo → `gradient-manager-compare`.

## Judgment notes

- **The memo recommends; the committee decides.** Section 1 states a clear recommendation and the vote
  requested, but the memo never says a decision "has been made".
- **Expected return and risk are assumptions, not forecasts.** Always name the CMA release and assumption set,
  and show the CMA consensus comparison next to Gradient's figures.
- **Uncertainty is shown, not hidden.** If data is illustrative, stale, or degraded, the reader must see that
  in the header and the affected section, not only in the appendix.
- **Attribution must reconcile.** Allocation + selection + interaction must sum to total active return within
  1 bp (or the residual is shown as its own row). If it doesn't reconcile, say so.
- **Liquidity is assessed under stress, not only today.** Always show coverage of unfunded commitments plus
  12 months of projected spending under the base case and the stress case the data supports.
