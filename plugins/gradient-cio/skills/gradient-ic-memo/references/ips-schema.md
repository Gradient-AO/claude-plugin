# IPS Schema

Use this shape only to organize quoted Investment Policy Statement evidence. Copy limits exactly as written
and record the IPS section reference for each so Section 4's Source column can cite it (`IPS §x.y`). Omit a
block entirely if the IPS does not address it — do not create defaults. Do not calculate compliance from this
local extraction. Governed statuses come from `check_portfolio_policy`; when the document differs from or is
not represented in the governed profile, disclose the difference and mark the affected row Not assessed.

```json
{
  "ips_name": "Example Foundation IPS",
  "ips_date": "2026-03-15",
  "allocation_bands": [
    {"asset_class": "public_equity", "target": 0.45, "min": 0.35, "max": 0.55, "ref": "IPS §4.1"}
  ],
  "return_objective": {
    "type": "nominal",              // "nominal" | "real" (real = CPI + spread)
    "value": 0.07,                  // nominal return, or the spread over CPI if type = real
    "cpi_assumption": null,         // required if type = real and the IPS states one
    "horizon_years": 10,
    "ref": "IPS §3.1"
  },
  "risk_limits": [
    {"metric": "volatility", "max": 0.14, "ref": "IPS §3.2"},
    {"metric": "max_drawdown", "max": 0.30, "ref": "IPS §3.2"},
    {"metric": "cvar_95_1y", "max": 0.20, "ref": "IPS §3.2"},
    {"metric": "tracking_error", "max": 0.04, "ref": "IPS §3.3"}
  ],
  "liquidity": [
    {"metric": "t1_min_pct_nav", "min": 0.15, "ref": "IPS §5.1"},
    {"metric": "illiquid_max_pct_nav_incl_unfunded", "max": 0.35, "ref": "IPS §5.2"},
    {"metric": "coverage_ratio_min", "min": 1.5, "ref": "IPS §5.3"}
  ],
  "concentration": [
    {"metric": "single_manager_max_pct_nav", "max": 0.10, "ref": "IPS §6.1"},
    {"metric": "top5_managers_max_pct_nav", "max": 0.40, "ref": "IPS §6.1"},
    {"metric": "single_security_max_pct_nav", "max": 0.05, "ref": "IPS §6.2"}
  ],
  "leverage": {"max_gross_pct_nav": 1.10, "ref": "IPS §6.3"},
  "restrictions": [
    {"description": "No direct tobacco holdings", "type": "prohibited", "ref": "IPS §7.1"}
  ],
  "other": [
    {"description": "Rebalance when any class exceeds its band", "type": "process", "ref": "IPS §4.3"}
  ]
}
```

## Field rules

- **Weights and rates are decimals** (0.45 = 45%). Convert any percentage text from the IPS.
- **Asset class keys** use Gradient's canonical identifiers (`public_equity`, `fixed_income`, `private_equity`,
  `private_credit`, `real_assets`, `real_estate`, `infrastructure`, `natural_resources`, `hedge_funds`,
  `absolute_return`, `cash`, `other`). If the IPS uses other categories, map them and list the mapping in
  Appendix B; if a mapping is ambiguous, keep the IPS label and mark the row `Not assessed — mapping unclear`.
- **Restrictions and other** cannot be tested numerically; they become rows with status `Not assessed` unless
  Gradient data directly evidences compliance or a breach (for example a prohibited holding appearing in the
  look-through), in which case cite it.
- **Real return objectives**: compare expected nominal return with CPI assumption + spread. If no CPI
  assumption is stated in the IPS, use the CMA release's inflation assumption if Gradient returns one and
  record it in Appendix B; otherwise mark `Not assessed — no inflation assumption`.
- Keep the original IPS wording for the "IPS requirement" column (for example "35%–55%", "≤ 14% volatility").
