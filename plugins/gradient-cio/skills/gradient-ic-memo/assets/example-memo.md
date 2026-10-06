# Investment Committee Memo — Rebalance: Gradient Global Growth III (Illustrative, Gradient Maintained)

> **ILLUSTRATIVE DATA** — Figures marked [S#] with scope "Illustrative, Gradient Maintained" describe a
> Gradient-maintained example portfolio, not the organization's actual holdings.

| Field | Value |
|---|---|
| Memo type | Rebalance |
| Portfolio | Gradient Global Growth III (example-portfolio-id; Illustrative, Gradient Maintained) |
| Organization | Example Foundation |
| Prepared for | Investment Committee |
| Meeting date | 2026-10-15 |
| Data as of | 2026-09-30 |
| Assumption set | Gradient ICAPM Global Baseline, Q3 2026 (USD) — CMA release Q3-2026-policy-v2.1 (2026-09-11) |
| Base currency | USD |
| Status | DRAFT — for committee review |
| Data quality | Illustrative |

## 1. Recommendation and Decision Requested

**Recommendation:** Reduce public equity by 400 bps to 48.0% and add 400 bps to cash (200 bps) and fixed income (200 bps) to cure two IPS band breaches.

**Decision requested:** The Committee is asked to approve the rebalance in Section 13.1, executed over 30 days.

**Rationale (three points, most important first):**
1. Fixed income (19.0%) and cash (1.0%) are below their IPS minimums [S1].
2. Cash at 1.0% leaves no operating buffer for 12-month calls of USD 180.0m [S1] [S9].
3. The change lowers expected volatility by 60 bps with a 15 bps reduction in expected return [S3].

**Key risks (three points, most material first):**
1. Risk-limit compliance is not assessed because the persisted thresholds do not specify a governed observation horizon and return basis [S1].
2. Expected return remains 28 bps below the CPI + 4.5% objective [S1] [S3].
3. Gradient's real estate assumption is 499 bps above consensus [S4].

**Conditions to approval:**
1. Confirm the inflation assumption used for the real return objective (Section 15, item 1).

## 2. Executive Summary

- **Positioning:** Public equity is 700 bps overweight and fixed income 600 bps underweight versus policy [S1].
- **IPS:** 6 constraints Compliant, 1 Watch, 2 Breach, 3 Not assessed. Breaches: fixed income band and cash band.
- **Performance:** 1Y return 6.9% versus 6.4% for the policy benchmark (+49 bps). Governed attribution is unavailable for the selected period [S2].
- **Outlook:** Expected return 6.7% versus a 7.0% objective, volatility 13.1%, 44.0% probability of meeting the objective [S3].
- **Liquidity & diligence:** Stress coverage 2.61 on the liquidity model; zero High diligence findings [S1] [S5] [S9].

## 3. Portfolio Snapshot

| Item | Value | Source |
|---|---|---|
| Total NAV | USD 3375.0m | [S1] |
| Unfunded commitments | USD 420.0m | [S1] |
| Number of holdings / commitments | 56 | [S1] |
| Number of managers | 18 | [S1] |
| Valuation date(s) | 2026-09-30; private funds 2026-06-30 (one quarter lag) | [S1] |

| Asset class | Current weight | Policy target | Range (min–max) | Active (bps) | Status |
|---|---|---|---|---|---|
| public_equity | 52.0% | 45.0% | 35.0%–55.0% | +700 bps | Compliant |
| fixed_income | 19.0% | 25.0% | 20.0%–30.0% | −600 bps | Breach |
| private_equity | 17.0% | 15.0% | 10.0%–20.0% | +200 bps | Compliant |
| real_estate | 11.0% | 10.0% | 5.0%–12.0% | +100 bps | Compliant |
| cash | 1.0% | 5.0% | 2.0%–8.0% | −400 bps | Breach |
| Total | 100.0% | 100.0% | | | |

## 4. IPS Compliance

| # | Constraint | IPS requirement | Current | Status | Source |
|---|---|---|---|---|---|
| 1 | Allocation — public_equity | 35.0%–55.0% | 52.0% | Compliant | IPS §4.1 |
| 2 | Allocation — fixed_income | 20.0%–30.0% | 19.0% | Breach | IPS §4.1 |
| 3 | Allocation — private_equity | 10.0%–20.0% | 17.0% | Compliant | IPS §4.1 |
| 4 | Allocation — real_estate | 5.0%–12.0% | 11.0% | Compliant | IPS §4.1 |
| 5 | Allocation — cash | 2.0%–8.0% | 1.0% | Breach | IPS §4.1 |
| 6 | Return objective | CPI + 4.5% | 6.7% | Watch | IPS §3.1 |
| 7 | Expected volatility | ≤ 14.0% | Not available — observation basis unaligned | Not assessed | IPS §3.2 |
| 8 | Expected max drawdown | ≤ 35.0% | Not available — observation basis unaligned | Not assessed | IPS §3.2 |
| 9 | T1 liquidity (% NAV) | ≥ 15.0% | 21.0% | Compliant | IPS §5.1 |
| 10 | Liquidity coverage ratio | ≥ 1.50 | 2.61 | Compliant | IPS §5.3 |
| 11 | Largest single manager (% NAV) | ≤ 10.0% | 8.5% | Compliant | IPS §6.1 |
| 12 | No direct tobacco holdings | prohibited | n/a | Not assessed | IPS §7.1 |

**Summary:** 6 Compliant, 1 Watch, 2 Breach, 3 Not assessed.
**Breaches and required actions:** Fixed income and cash bands — cured by the Section 13 rebalance.

## 5. Performance & Attribution

**5.1 Returns**

| Period | Portfolio | Policy benchmark | Excess (bps) | Basis |
|---|---|---|---|---|
| QTD | 1.8% | 1.6% | +20 bps | Net |
| YTD | 5.2% | 4.9% | +30 bps | Net |
| 1Y | 6.9% | 6.4% | +49 bps | Net |
| 3Y ann. | 7.4% | 7.1% | +30 bps | Net |
| 5Y ann. | n/a | n/a | n/a | Net |
| Since inception ann. | 7.0% | 6.8% | +20 bps | Net |

**5.2 Attribution — 1Y**

Not available — `get_portfolio_attribution` returned `coverage.status: unavailable` with
`no_weight_cohorts`; no local attribution was derived [S2].

**5.3 Top contributors and detractors**

| Rank | Contributors | Contribution (bps) | Detractors | Contribution (bps) |
|---|---|---|---|---|
| 1 | Manager A (public equity) | +31 bps | Manager F (buyout) | −14 bps |
| 2 | Manager B (public equity) | +12 bps | Manager G (core bonds) | −6 bps |

## 6. Factor Exposures & Concentration

**6.1 Factor exposures**

| Factor | Exposure | Benchmark exposure | Active | Units | Source |
|---|---|---|---|---|---|
| Equity market | 0.78 | 0.70 | 0.08 | beta | [S6] |
| Duration | 1.90 | 2.40 | −0.50 | years | [S6] |

**6.2 Concentration and diversification**

| Metric | Value | IPS limit | Status | Source |
|---|---|---|---|---|
| Largest single manager (% NAV) | 8.5% | 10.0% | Compliant | [S1] |
| Top 5 managers (% NAV) | 34.0% | n/a | Not assessed | [S1] |
| Largest single holding look-through (% NAV) | n/a | n/a | Not assessed | Not available — no look-through data |
| Effective number of positions | 14.20 | n/a | n/a | [S6] |
| Diversification ratio | 1.32 | n/a | n/a | [S6] |
| Equity beta to global equities | 0.78 | n/a | Not assessed | [S6] |

## 7. Expected Return & Risk

**Assumptions:** Gradient ICAPM Global Baseline Q3 2026, CMA release Q3-2026-policy-v2.1, 10-year horizon, USD, unhedged.

**7.1 Portfolio expected statistics**

| Metric | Current | Proposed | Policy portfolio | IPS objective / limit | Status |
|---|---|---|---|---|---|
| Expected return (nominal, ann.) | 6.7% | 6.6% | 6.5% | 7.0% | Watch |
| Expected excess return over cash | 2.9% | 2.8% | 2.7% | n/a | n/a |
| Expected volatility (ann.) | 13.1% | 12.5% | 12.0% | 14.0% | Watch |
| Sharpe ratio | 0.22 | 0.22 | 0.23 | n/a | n/a |
| Expected max drawdown | 38.0% | 36.5% | 35.0% | 35.0% | Breach |
| 95% CVaR (1-year) | 21.0% | 20.0% | 19.5% | n/a | Not assessed |
| Probability of meeting return objective | 44.0% | 42.0% | 40.0% | n/a | n/a |

**7.2 Consensus check**

| Asset class | Gradient expected excess | Consensus reference | Gap (bps) | Comparability | Source |
|---|---|---|---|---|---|
| public_equity | 4.7% | 5.1% | −34 bps | proxy | [S4] |
| real_estate | 7.6% | 2.6% | +499 bps | direct | [S4] |

**Allocation-implied return:** Gradient 8.2% vs consensus 6.7% (Example consultant CMA survey, 2025-12-31) [S4].
**Assumption quality:** quality receipt unvalidated; repeated higher moments flagged for two equity factors [S4].

**7.3 Regime overlay**

**Current regime:** GRIP 76 (Defensive), as of 2026-10-01, coverage 0.95, degraded (one lagging input) [S7].
**Effect on expectations:** Regime adjustment not available — baseline shown.

## 8. Stress Tests & Scenarios

| Scenario | Type | Portfolio impact | Policy impact | Liquidity coverage after | Source |
|---|---|---|---|---|---|
| 2008 global financial crisis | Historical | −24.0% | −21.0% | 2.61 | [S8] |
| 5th percentile, 1 year | Simulated percentile | −14.0% | −12.5% | 3.80 | [S8] |

**Robustness:** Results are stable across start dates within ±80 bps of expected return [S8].

## 9. Liquidity

**9.1 Liquidity tiers**

| Tier | Definition | % NAV | Amount (USD m) | Source |
|---|---|---|---|---|
| T1 | Daily to weekly | 44.6% | 1505.0 | [S1] |
| T2 | Monthly to quarterly | 11.9% | 400.0 | [S1] |
| T3 | Semi-annual to 2 years | 11.9% | 400.0 | [S1] |
| T4 | Over 2 years / locked / private | 31.7% | 1070.0 | [S1] |
| Total | | 100.0% | 3375.0 | |

**9.2 Coverage**

| Metric | Base case | Stress case | IPS minimum | Status | Source |
|---|---|---|---|---|---|
| T1 liquidity (% NAV) | 44.6% | 42.4% | 15.0% | Compliant | [S1] [S11] |
| Unfunded commitments (USD m) | 420.0 | 420.0 | n/a | n/a | [S1] |
| 12-month spending / distributions (USD m) | 150.0 | 150.0 | n/a | n/a | [S1] |
| Liquidity coverage ratio | 5.77 | 2.61 | 1.50 | Compliant | [S1] [S11] |
| Private markets % NAV (incl. unfunded) | 36.1% | 36.1% | 40.0% | Watch | [S1] |

- HF B placed in T4 (gated).

**Pacing:** Projected 12-month calls USD 180.0m against distributions of USD 95.0m [S9].

## 10. Manager & Operational Diligence

| Manager | Strategy | Exposure (% NAV) | ODD red flags | Open findings (H/M/L) | Monitor alerts | GIPS status | Last review | Source |
|---|---|---|---|---|---|---|---|---|
| Manager A | Global equity | 8.5% | 0 | 0/1/0 | 0 | Claims, verified | 2026-06-30 | [S5] |
| Other (17 managers) | Various | 91.5% | n/a | 0/2/3 | 0 | n/a | n/a | [S5] |

**Exposure-weighted findings:** No active High findings [S5].
**Attention queue:** None overdue [S5].

## 11. Performance Integrity & GIPS

### 11.1 Total fund
Not assessed — no GIPS Asset Owner Report provided.

### 11.2 Manager A
**Overall assessment:** Satisfactory with follow-ups. Verification report for the latest year not yet received.

## 12. Market Context

- **Regime:** GRIP 76, Defensive; rates and cross-asset pillars are the main pressure [S7].
- **Key indicators:** Core PCE index rose 0.3% over three months [S10].
- **Current thesis:** Diesel margins carry the Gulf energy premium; confirm above USD 102/bbl crack [S10].
- **Upcoming catalysts:** US CPI on 2026-10-14; FOMC on 2026-10-28 [S10].

## 13. Proposed Changes & Impact

**13.1 Allocation change**

| Asset class / manager | Current | Proposed | Change (bps) | Funding source | IPS status after |
|---|---|---|---|---|---|
| public_equity | 52.0% | 48.0% | −400 bps | Index fund | Compliant |
| fixed_income | 19.0% | 21.0% | +200 bps | Public equity | Compliant |
| cash | 1.0% | 3.0% | +200 bps | Public equity | Compliant |

**13.2 Impact summary**

| Measure | Current | Proposed | Change | Source |
|---|---|---|---|---|
| Expected return | 6.7% | 6.6% | −15 bps | [S3] |
| Expected volatility | 13.1% | 12.5% | −60 bps | [S3] |
| Sharpe ratio | 0.22 | 0.22 | 0.00 | [S3] |
| T1 liquidity (% NAV) | 44.6% | 46.6% | +200 bps | [S11] |
| Liquidity coverage ratio | 2.61 | 2.70 | 0.09 | [S11] |
| IPS breaches | 2 | 0 | −2 | [S11] |
| Estimated transaction cost (bps) | n/a | 3 bps | +3 bps | [S11] |

**Implementation:** Sell the index fund in two tranches over 30 days; buy core bonds and Treasury bills [S11].
**Alternatives considered:** No change — rejected because two band breaches and the coverage breach would remain. Full rebalance to policy — rejected because it would sell 700 bps of equity into a Defensive regime in one step.

## 14. Risks & Mitigants

| # | Risk | Rating | Evidence | Mitigant | Owner |
|---|---|---|---|---|---|
| 1 | Risk-limit compliance not assessed | Medium | Persisted thresholds lack a governed observation horizon and return basis [S1] | Approve an observation basis before evaluating volatility, drawdown or CVaR compliance | CIO |
| 2 | Real estate CMA well above consensus | Medium | +499 bps gap [S4] | Run Section 7 with consensus real estate assumption before the next review | Analyst |
| 3 | Return objective shortfall | Low | −28 bps [S3] | Revisit spending policy at the annual review | Committee |

## 15. Open Items & Conditions

| # | Item | Reason | Timing | Owner |
|---|---|---|---|---|
| 1 | Confirm inflation assumption for real return objective | IPS does not state one | Before approval | CIO |
| 2 | Provide look-through holdings | Not available | Next review | Operations |
| 3 | Obtain Manager A verification report | GIPS follow-up | Within 30 days | Analyst |
| 4 | Provide GIPS Asset Owner Report | Not provided | Next review | Operations |
| 5 | Define the governed policy-risk observation horizon and return basis | Risk rows are not assessed without aligned observations | Next review | CIO |

## 16. Approvals

| Role | Name | Decision | Date |
|---|---|---|---|
| Prepared by | | n/a | |
| Reviewed by (CIO) | | | |
| Committee chair | | | |

---

## Appendix A — Sources

| Ref | Source | Parameters | As of | Data scope | Validation | Digest |
|---|---|---|---|---|---|---|
| S1 | get_portfolio_exposure; get_portfolio_structure; check_portfolio_policy | portfolio_id=example; governed policy and exposure views | 2026-09-30 | Illustrative, Gradient Maintained | passed | n/a |
| S2 | get_portfolio_historical_returns; get_portfolio_attribution | portfolio_id=example; policy benchmark; performance available; attribution unavailable (`no_weight_cohorts`) | 2026-09-30 | Illustrative, Gradient Maintained | partial | n/a |
| S3 | get_chart_data | portfolio_id=example; analysis_type=expected-statistics | 2026-09-11 | Illustrative, Gradient Maintained | passed | n/a |
| S4 | get_cma_consensus_check | mode=allocation | 2026-06-30 | Mixed — Illustrative, Gradient Maintained + User-Authorized Live | passed | n/a |
| S5 | get_manager_diligence_findings | view=exposure_weighted | 2026-10-02 | Illustrative, Gradient Maintained | advisory | n/a |
| S6 | get_chart_data | portfolio_id=example; analysis_type=allocations | 2026-09-30 | Illustrative, Gradient Maintained | passed | n/a |
| S7 | get_macro_signals | view=gradient_signal (sources.grip) | 2026-10-01 | User-Authorized Live | passed | n/a |
| S8 | Illustrative scenario assumptions | 2008 historical; 5th percentile | 2026-09-30 | Illustrative, Gradient Maintained | not applicable | n/a |
| S9 | get_chart_data | portfolio_id=example; analysis_type=commitments | 2026-06-30 | Illustrative, Gradient Maintained | passed | n/a |
| S10 | get_macro_conditions; get_the_read; get_macro_calendar | theme=inflation; am edition; 30 days | 2026-10-02 | User-Authorized Live | passed | n/a |
| S11 | Server-returned illustrative proposed-case analysis | target weights and implementation estimate per Section 13.1 | 2026-09-30 | Illustrative, Gradient Maintained | passed | n/a |

## Appendix B — Server Metric Methods

| Source | Quantity | Method / formula ID | Version | Basis and tolerance |
|---|---|---|---|---|
| S1 | IPS status, active weights, liquidity and concentration | check_portfolio_policy | 2026-10-05.v1 | Governed inputs only; preserve returned thresholds and coverage |
| S2 | Realized returns and risk | get_portfolio_historical_returns | as returned | Preserve period labels, annualization, benchmark basis, units and coverage |
| S2 | Realized attribution | Not available | n/a | `no_weight_cohorts`; no formula or result asserted |
| S6 | Effective number of positions | Portfolio Analytics allocations metric | as returned | Preserve chart-pack basis and fingerprint |
| S11 | Proposed-case impacts | Portfolio Analytics proposed-case analysis | as returned | Same basis as current case |

## Appendix C — Methodology & Disclosures

- Expected returns and risk are forward-looking assumptions from Gradient ICAPM Global Baseline Q3 2026, not forecasts or guarantees. Actual results will differ.
- Performance is shown net of manager fees. Periods over one year are annualized.
- Attribution is unavailable for this example because no governed segment-weight cohort was returned; no local fallback is used. Factor model: Portfolio Analytics factor/currency exposure.
- Private-markets valuations may lag by 3 months; values as of 2026-06-30.
- Data sources and retrieval dates are listed in Appendix A. Sections using illustrative data are marked; they do not describe the organization's holdings.
- GIPS assessments are diligence reviews against the 2020 GIPS standards, not verifications or legal opinions.
- This memo was prepared with AI assistance from structured data and reviewed by the preparer.
