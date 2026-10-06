# IC Memo Template (authoritative)

Copy this structure exactly. Text in `<angle brackets>` is replaced; text in `{braces}` is a rule, not output.
Headings, numbering, table columns and column order never change. If a section has no data, keep the heading
and write the `Not available` line shown for it.

Contents: Header · 1 Recommendation · 2 Executive Summary · 3 Portfolio Snapshot · 4 IPS Compliance ·
5 Performance & Attribution · 6 Factor Exposures & Concentration · 7 Expected Return & Risk ·
8 Stress Tests & Scenarios · 9 Liquidity · 10 Manager & Operational Diligence · 11 Performance Integrity & GIPS ·
12 Market Context · 13 Proposed Changes & Impact · 14 Risks & Mitigants · 15 Open Items & Conditions ·
16 Approvals · Appendix A Sources · Appendix B Calculations · Appendix C Methodology & Disclosures

---

```
# Investment Committee Memo — <Memo type>: <Portfolio name>

{If any source has data_scope.kind = illustrative, insert this line verbatim, else omit:}
> **ILLUSTRATIVE DATA** — Figures marked [S#] with scope "Illustrative, Gradient Maintained" describe a
> Gradient-maintained example portfolio, not the organization's actual holdings.

| Field | Value |
|---|---|
| Memo type | <Portfolio Review / Allocation Change / Rebalance / Manager Hire / Manager Termination / New Commitment> |
| Portfolio | <name> (<portfolio id>) |
| Organization | <organization name returned by Gradient> |
| Prepared for | <IC / Board / Trustees / Client name> |
| Meeting date | <YYYY-MM-DD or "Not specified"> |
| Data as of | <YYYY-MM-DD> |
| Assumption set | <assumption set name> — CMA release <version> (<release date>) |
| Base currency | <ISO code> |
| Status | DRAFT — for committee review |
| Data quality | <Complete / Degraded — <n> sections affected / Illustrative> |
```

## 1. Recommendation and Decision Requested

```
**Recommendation:** <one sentence: the action, the amount or weight, the subject>.

**Decision requested:** The Committee is asked to <approve / note / reject> <specific resolution>.

**Rationale (three points, most important first):**
1. <reason> [S#]
2. <reason> [S#]
3. <reason> [S#]

**Key risks (three points, most material first):**
1. <risk> [S#]
2. <risk> [S#]
3. <risk> [S#]

**Conditions to approval:** <numbered list from Section 15 marked "Before approval", or "None">.
```

{Portfolio Review with no proposed change: Recommendation = "Maintain the current allocation" or the
specific change Section 13 supports. Decision requested = "note the review" unless an IPS breach requires action.}

## 2. Executive Summary

Exactly five bullets, in this order, one to two sentences each:

```
- **Positioning:** <current allocation vs policy in one sentence> [S#]
- **IPS:** <n> constraints Compliant, <n> Watch, <n> Breach, <n> Not assessed. <Name any Breach.>
- **Performance:** <primary period return vs policy benchmark, excess in bps, main attribution driver> [S#]
- **Outlook:** <expected return vs IPS objective, expected volatility, probability of meeting objective> [S#]
- **Liquidity & diligence:** <liquidity coverage ratio and status; number of High diligence findings> [S#]
```

## 3. Portfolio Snapshot

```
| Item | Value | Source |
|---|---|---|
| Total NAV | <currency> <x.x>m | [S#] |
| Unfunded commitments | <currency> <x.x>m | [S#] |
| Number of holdings / commitments | <n> | [S#] |
| Number of managers | <n> | [S#] |
| Valuation date(s) | <YYYY-MM-DD; note any lagged private valuations> | [S#] |
```

**Asset allocation** {sort: by policy target weight descending, then name; final row "Total"}

```
| Asset class | Current weight | Policy target | Range (min–max) | Active (bps) | Status |
|---|---|---|---|---|---|
```

{Status uses the IPS band rule in calculations.md. If no IPS: Policy target, Range, Status = "Not assessed".}

## 4. IPS Compliance

{One row per constraint in the IPS, in IPS-schema order: allocation bands, return objective, risk limits,
liquidity, concentration, leverage, prohibited/restricted, ESG/other. Governed rows come from
`check_portfolio_policy`; keep unsupported document-only constraints Not assessed.}

```
| # | Constraint | IPS requirement | Current | Status | Source |
|---|---|---|---|---|---|
```

**Status values (only these):** `Compliant` · `Watch` · `Breach` · `Not assessed`

```
**Summary:** <n> Compliant, <n> Watch, <n> Breach, <n> Not assessed.
**Breaches and required actions:** <one line per Breach with the cure proposed in Section 13, or "None">.
```

{If no IPS: single row "IPS not provided" with Status "Not assessed", and add "Provide IPS" to Section 15.}

## 5. Performance & Attribution

**5.1 Returns** {periods fixed: QTD, YTD, 1Y, 3Y ann., 5Y ann., Since inception ann.; missing → "n/a"}

```
| Period | Portfolio | Policy benchmark | Excess (bps) | Basis |
|---|---|---|---|---|
```

{Basis = "Net" or "Gross" exactly as returned; never mix bases in one row.}

**5.2 Attribution — <period>** {sort: by |total effect| descending; final rows "Residual" (if any) and "Total"}

```
| Asset class | Allocation (bps) | Selection (bps) | Interaction (bps) | Total (bps) |
|---|---|---|---|---|
```

```
**Reconciliation:** Sum of effects = <x> bps vs total active return <y> bps; residual <z> bps [S#].
**Method:** <server-returned attribution method, linking method, period/basis/currency and formula version>.
```

**5.3 Top contributors and detractors** {five each, sorted by contribution; ties by name}

```
| Rank | Contributors | Contribution (bps) | Detractors | Contribution (bps) |
|---|---|---|---|---|
```

## 6. Factor Exposures & Concentration

**6.1 Factor exposures** {sort: by |exposure| descending}

```
| Factor | Exposure | Benchmark exposure | Active | Units | Source |
|---|---|---|---|---|---|
```

**6.2 Concentration and diversification**

```
| Metric | Value | IPS limit | Status | Source |
|---|---|---|---|---|
| Largest single manager (% NAV) | | | | |
| Top 5 managers (% NAV) | | | | |
| Largest single holding look-through (% NAV) | | | | |
| Effective number of positions | | n/a | n/a | |
| Diversification ratio | | n/a | n/a | |
| Equity beta to <benchmark> | | | | |
```

## 7. Expected Return & Risk

{Name the CMA release and assumption set in the first line. Horizon as returned (default 10 years).}

```
**Assumptions:** <assumption set>, CMA release <version>, <horizon>-year horizon, <base currency>, <hedging>.
```

**7.1 Portfolio expected statistics** {columns fixed; "Proposed" = "n/a" if Section 13 has no change; Status applies to the Current column and must match Section 4}

```
| Metric | Current | Proposed | Policy portfolio | IPS objective / limit | Status |
|---|---|---|---|---|---|
| Expected return (nominal, ann.) | | | | | |
| Expected excess return over cash | | | | | |
| Expected volatility (ann.) | | | | | |
| Sharpe ratio | | | | n/a | n/a |
| Expected max drawdown | | | | | |
| 95% CVaR (1-year) | | | | | |
| Probability of meeting return objective | | | | n/a | n/a |
```

**7.2 Consensus check** {from get_cma_consensus_check; one row per asset class held}

```
| Asset class | Gradient expected excess | Consensus reference | Gap (bps) | Comparability | Source |
|---|---|---|---|---|---|
```

```
**Allocation-implied return:** Gradient <x.x>% vs consensus <y.y>% (<publisher>, <date>) [S#].
**Assumption quality:** <quality_receipt status and any governance flags, or "No flags">.
```

**7.3 Regime overlay**

```
**Current regime:** GRIP <score> (<stance>), as of <date>, data <coverage/degradation> [S#].
**Effect on expectations:** <regime-adjusted vs baseline figures if returned, else "Regime adjustment not
available — baseline shown">.
```

## 8. Stress Tests & Scenarios

{sort: by portfolio impact ascending (worst first)}

```
| Scenario | Type | Portfolio impact | Policy impact | Liquidity coverage after | Source |
|---|---|---|---|---|---|
```

{Type = Historical / Hypothetical / Simulated percentile / Date-window robustness.}

```
**Robustness:** <date-window robustness result in one sentence> [S#].
```

## 9. Liquidity

**9.1 Liquidity tiers** {tiers fixed, in this order}

```
| Tier | Definition | % NAV | Amount (<ccy> m) | Source |
|---|---|---|---|---|
| T1 | Daily to weekly | | | |
| T2 | Monthly to quarterly | | | |
| T3 | Semi-annual to 2 years | | | |
| T4 | Over 2 years / locked / private | | | |
| Total | | 100.0% | | |
```

**9.2 Coverage**

```
| Metric | Base case | Stress case | IPS minimum | Status | Source |
|---|---|---|---|---|---|
| T1 liquidity (% NAV) | | | | | |
| Unfunded commitments (<ccy> m) | | | n/a | n/a | |
| 12-month spending / distributions (<ccy> m) | | | n/a | n/a | |
| Liquidity coverage ratio | | | | | |
| Private markets % NAV (incl. unfunded) | | | | | |
```

```
**Pacing:** <next 12 months projected calls and distributions, or "Pacing data not available">.
```

## 10. Manager & Operational Diligence

{One row per manager with ≥ 1% of NAV; sort by exposure descending; "Other (<n> managers)" as last row.}

```
| Manager | Strategy | Exposure (% NAV) | ODD red flags | Open findings (H/M/L) | Monitor alerts | GIPS status | Last review | Source |
|---|---|---|---|---|---|---|---|---|
```

```
**Exposure-weighted findings:** <top findings ranked by exposure, or "No active findings"> [S#].
**Attention queue:** <managers overdue for review, or "None overdue"> [S#].
```

## 11. Performance Integrity & GIPS

{Paste sections from gradient-gips-asset-owner-review (total fund) and gradient-gips-manager-diligence (each manager ≥ 5% NAV or
being hired), unchanged, ordered: total fund first, then managers by exposure descending.}

```
### 11.1 Total fund
<gradient-gips-asset-owner-review oversight-body summary, or "Not assessed — <reason>">

### 11.2 <Manager name>
<gradient-gips-manager-diligence memo section>
```

## 12. Market Context

{At most 150 words. Facts only from Gradient tools; no forecasts.}

```
- **Regime:** <GRIP stance and top two pillar drivers> [S#]
- **Key indicators:** <two or three macro readings relevant to the portfolio> [S#]
- **Current thesis:** <The Read headline and its confirm/refute thresholds> [S#]
- **Upcoming catalysts:** <next two scheduled events from the macro calendar> [S#]
```

## 13. Proposed Changes & Impact

{If no change: "No change proposed." and keep both tables with the Current column only filled.}

**13.1 Allocation change** {sort: by |change| descending}

```
| Asset class / manager | Current | Proposed | Change (bps) | Funding source | IPS status after |
|---|---|---|---|---|---|
```

**13.2 Impact summary**

```
| Measure | Current | Proposed | Change | Source |
|---|---|---|---|---|
| Expected return | | | | |
| Expected volatility | | | | |
| Sharpe ratio | | | | |
| T1 liquidity (% NAV) | | | | |
| Liquidity coverage ratio | | | | |
| IPS breaches | | | | |
| Estimated transaction cost (bps) | | | | |
```

```
**Implementation:** <sequencing, timing, rebalancing method> [S#].
**Alternatives considered:** <at least one alternative and why it was not recommended>.
```

## 14. Risks & Mitigants

{sort: High, then Medium, then Low; within a rating, by section order. Include every High/Medium GIPS finding.}

```
| # | Risk | Rating | Evidence | Mitigant | Owner |
|---|---|---|---|---|---|
```

**Rating values (only these):** `High` · `Medium` · `Low`

## 15. Open Items & Conditions

{Every "Not available" item, every GIPS follow-up, every Watch/Breach action. Timing values only:
"Before approval" · "Within 30 days" · "Next review".}

```
| # | Item | Reason | Timing | Owner |
|---|---|---|---|---|
```

## 16. Approvals

```
| Role | Name | Decision | Date |
|---|---|---|---|
| Prepared by | | n/a | |
| Reviewed by (CIO) | | | |
| Committee chair | | | |
```

---

## Appendix A — Sources

{One row per tool call or document used; S-numbers assigned in order of first citation.}

```
| Ref | Source | Parameters | As of | Data scope | Validation | Digest |
|---|---|---|---|---|---|---|
```

## Appendix B — Server Metric Methods

```
| Source | Quantity | Method / formula ID | Version | Basis and tolerance |
|---|---|---|---|---|
```

## Appendix C — Methodology & Disclosures

{Fixed text; fill the brackets.}

```
- Expected returns and risk are forward-looking assumptions from <assumption set / CMA release>, not forecasts
  or guarantees. Actual results will differ.
- Performance is shown <net / gross> of <fees deducted>. Periods over one year are annualized.
- Attribution method: <method>. Factor model: <model name and version>.
- Private-markets valuations may lag by <n> months; values as of <date>.
- Data sources and retrieval dates are listed in Appendix A. <If illustrative data: "Sections using
  illustrative data are marked; they do not describe the organization's holdings.">
- GIPS assessments are diligence reviews against the 2020 GIPS standards, not verifications or legal opinions.
- This memo was prepared with AI assistance from structured data and reviewed by <preparer>.
```
