---
name: gradient-ic-memo
description: Write a deterministic, fully sourced investment committee (IC) memo for a portfolio, total fund, allocation change, rebalance, or manager hire/fire, using GradientCIO data (portfolio exposure, Strategy Lab attribution, factor loads, expected statistics, simulations, CMAs, liquidity, manager diligence) and the gradient-gips-* skills. Delivers a branded PDF memo in the Gradient house style. Use this skill whenever the user asks for an IC memo, investment committee memo, board memo, investment memo, committee paper, allocation recommendation, rebalance proposal, a portfolio review that ends in a decision or vote, IPS compliance review, or a client or trustee memo about a portfolio — even if they don't say "IC memo". Also use it when another skill (such as gradient-gips-manager-diligence) hands over a section "for the investment memo". For a periodic performance report with no decision requested, use gradient-portfolio-review instead.
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
| `references/chart-data.md` | Always — dashboard chart discovery, basis rules and generic report block. |
| `references/ips-schema.md` | When an IPS is supplied or needed — how to capture IPS constraints as structured input. |
| `references/calculations.md` | Before computing anything — the only formulas allowed, rounding and status thresholds. |
| `references/writing-standards.md` | Before drafting prose — IC memo best practices and banned phrasing. |
| `scripts/memo_calcs.py` | For IPS checks, liquidity tiers, Brinson attribution and formatting. Run it; do not hand-compute. |
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
- Use `envelope: "compact"` where offered.
- Use `get_chart_data` after portfolio selection: check availability, then request one relevant pack at a time.
  Expected-statistics charts complement Strategy Lab outputs; they do not replace what-if analysis. Preserve
  `basis` and `context.fingerprint`, skip unavailable charts with their reason, and never compare different
  bases as though they were the same scenario.
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

### Step 4 — Calculate

Use `scripts/memo_calcs.py` for every derived number (see `references/calculations.md`). Typical run:

```bash
python scripts/memo_calcs.py ips      --input ips_and_allocation.json   # IPS compliance table
python scripts/memo_calcs.py liquidity --input liquidity.json           # liquidity tiers and coverage
python scripts/memo_calcs.py brinson  --input attribution_inputs.json   # only if no attribution from Strategy Lab
```

Prefer Strategy Lab outputs over local calculation. Calculate locally only when Gradient returns the inputs
but not the derived figure, and tag the result `[Calc C#]` with the formula listed in Appendix B.

### Step 5 — Draft the memo

Write the memo exactly as `references/memo-template.md` specifies, applying `references/writing-standards.md`.
Determinism rules (summary — the template is authoritative):

1. All 16 sections plus the appendices, in order, with the exact headings. Never add, remove, rename or reorder.
2. Every table uses the template's columns, in order, with the template's sort rule.
3. Missing data → `Not available — <reason>` in place of the value; the row stays.
4. Number formats follow `references/calculations.md` (percentages 1 dp, active weights and spreads in bps,
   currency in millions with 1 dp, ISO dates).
5. Every number in the text or a table carries a source tag: `[S#]` (Gradient / document) or `[Calc C#]`.
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

For an Allocation Change or Rebalance memo, offer to save the proposed scenario to Strategy Lab so the
committee can revisit it: `save_strategy_lab_scenario` (`domain` rebalance/optimization/simulation/relative,
`name` "<Portfolio> - <memo type> <meeting date>", the `form` and basket used in Section 13). Call with
`dry_run: true` first, show the preview, then repeat with `dry_run: false` and `confirmation_receipt_id` set to
the preview receipt only after the user confirms. Unavailable on illustrative access: say so instead.

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
