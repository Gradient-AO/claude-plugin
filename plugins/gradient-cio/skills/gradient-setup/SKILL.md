---
name: gradient-setup
description: "Create a readiness report for GradientCIO access and data. Triggers: 'check GradientCIO setup', 'test connector readiness', 'which workflows are ready'. For workflow selection use gradient-menu."
metadata:
  style_contract: "2.3.0"
  group: "Start"
  subject: "connection and readiness"
  output: "report"
  menu_order: "20"
  modules: "none"
  contracts: "none"
  handoffs: "gradient-menu"
  status: "core"
  summary: "Check connection, entitlements, contracts and data readiness."
---

# Gradient setup and readiness check

Before using any expected return, excess return, or Sharpe ratio, read `${CLAUDE_PLUGIN_ROOT}/shared/contracts/expected-return-sources.md` and apply its return-source, weight-basis, comparison, and risk-free-rate labels.
Use when the user is new to the Gradient skills, says "set up Gradient", "get started", "is Gradient connected", "what is ready for my organization", "check my access", "health check", "self-test", or another Gradient skill
fails because the connector is missing, unauthorized or returning errors. For only "what can I do?" or
"show commands", use `gradient-menu`. Also use this readiness check after a plugin update.
The deliverable is a short branded **"Gradient Readiness Report"**, plus a three-line chat summary and two or
three prompts the user can try next. Keep the language plain: the reader may not be technical.
Read `${CLAUDE_PLUGIN_ROOT}/shared/module-scope.md` before checking Portfolio Analytics or Strategy Lab. Test and
report them as separate modules; never use the canonical illustrative portfolio ID as Strategy Lab input.
## 1. Connection
1. Check that GradientCIO tools are available (search for `GradientCIO`). If none appear, the connector is not
   connected. The plugin bundles it (`https://mcp.gradientcio.com/mcp`), so tell the user to open their connector
   settings, find **GradientCIO** and sign in. Still produce the PDF with signal `not_ready` and the steps to fix.
2. Call `list_organizations`. An auth error means the sign-in expired or lacks scopes: ask the user to reconnect.
   If more than one organization is returned and the user has not named one, ask which to check.
   Record `licensed_modules` and `role`.
## 2. Access and data readiness
1. Call `get_gradient_capabilities` with the `organization_id` and `detail: "summary"`, omitting `scope`:
   - `product_entitlements` = commercial licenses; `capability_access_modes` = each capability's `live`,
     `illustrative`, or `unavailable` access basis; `effective_capabilities` = whether that mode is usable,
     including bounded illustrative access; each tool's `access_mode` and `available` are the final invocation
     basis and decision. Require all three maps and treat a false entitlement plus an `illustrative` capability
     mode as evaluation access, never as live licensed access;
   - `backend_readiness`, `version`;
   - `contract_identity.compatibility_epoch`;
   - per tool: `entitled`, `available`, `scoped`, `healthy`, `data_ready`, `availability_reason`,
     `missing_oauth_scopes`;
   - `coverage[]`: domain, status (`available`, `conditional`, `unavailable`), `as_of`.
   Summary intentionally omits per-backend readiness. Request `detail: "full"` only when
   diagnosing those details.
2. Save the summary response, then validate the machine-readable `minimum_connector_contract` in
   `references/contracts.json`:

   ```
   python <this skill's directory>/scripts/check_contract.py --validate-connector \
     <this skill's directory>/references/contracts.json <capabilities-response.json>
   ```

   This requires service version 0.11.0 or newer, compatibility epoch 4, every required public tool, and a
   coherent `capability_access_modes` map whose modes agree with `effective_capabilities`.
   On failure, stop before skill or probe execution, mark the connector `not_ready`, quote the validator
   failure, and tell the user to update or reconnect GradientCIO. Do not replace missing connector
   calculations with local calculations.
3. Map tools to skills with `references/skill-requirements.md`. A skill is **ready** when every required tool is
   entitled, available and healthy; **partial** when optional tools are missing or a degradable call failure
   leaves independent evidence available; **not available** when a required tool is not entitled (name the
   module the client would need to license). When `entitled` is false but `available` is true with
   `access_mode: "illustrative"`, report
   **Evaluation — Illustrative, Gradient Maintained — demo data, not the client's holdings or managers**,
   not Ready or Not licensed.
   Then apply `mode_requirements` for the selected allocation-study mode. Run
   `check_contract.py --validate-mode <contracts.json>
   gradient-allocation-study <mode> <capabilities-response.json>`. For
   portfolio import, validate `gradient-portfolio-import governed`.
4. Report workflow status separately from runtime readiness: Core, Blocked, or
   Paused. Do not probe Blocked or Paused workflows.
## 3. Contract self-test
Run the probes in `references/contract-checks.md`. The **standard** set is the
quick Core readiness set. The **full read** set adds only active Core probes;
run it when the user asks for a health
check or self-test, or after a plugin update. The separate **writes** set contains the Strategy Lab scenario dry-run preview and
must never commit. Private-markets construction adds one fictional `private_markets_holdings` read probe. The dedicated
**portfolio-import-governed** defines 11 schema-driven calls and requires an authorized source connector, one provider/account, and one existing Gradient portfolio. It covers all sixteen runtime types, including Phase 4 portfolio/allocation/policy records and Phase 5 public-security, fixed-income, liquidity, classification, pacing, and source-document-reference records through the generic staging path. Its safe
readiness path stops after preview plus session/history reads. Commit requires runtime "commit_enabled" treatment and current-conversation
confirmation of the exact displayed diff, issues, controls, digest and receipt; rollback requires a separate
explicit request with the exact destination-after digest. Monthly returns are month-end, source-reported
`EntityReturn` records only and never legacy JSONB; benchmark definitions precede dependent assignment
sessions; assignments target only portfolios, allocations, commitments, or overlays, with weights only on
allocations. A client-owned scheduled task may stage only with `approval_surface: "gradient_ui"` and return
`review_url`; every v1 run requires Gradient UI review and never auto-commits in Claude. This is connector
ingest, not Gradient UI file upload. The complete matrix is 32 active Core read calls, or 43
when all eleven governed portfolio-import definitions are authorized.
The full set must verify expected-return provenance inputs for policy
(`user × policy_targets`), ex-ante attribution
(`user × current_actual`), and CMA portfolio analytics
(`cma_implied × policy_targets` for this governed probe). For each probe, record pass, fail (with error code and HTTP status) or not run (not entitled), and the
response `as_of`. Resolve `depends_on` arguments with `check_contract.py --resolve-args`; do not manually
copy or invent chained IDs.

For a saved response file you can check required paths with
`python <this skill's directory>/scripts/check_contract.py <this skill's directory>/references/contracts.json <probe_id> <response.json>`.

Treat every failed probe as a finding: quote the error code, HTTP status and request ID so the user can send
it to Gradient support. Do not replace a failed result with a local calculation or infer an empty result.
## 4. Branding
Check the plugin's `branding.json` (plugin root). `brand: "gradient"` is the explicit default and renders
the GradientCIO mark. An empty `client_name` is intentional in the public marketplace package; it prevents a
client identity from shipping to every installer and is not an unbranded-report failure. Say how to apply
client branding: an administrator sets the client name and logo before distributing a private client build
(`python tools/set_branding.py` at the plugin root); for one report, give a name and logo in the conversation
and the skill renders with `--brand`.
## 5. Build the report
Write and validate `report.json` (JSON block mode, see `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md`). Select PDF by default;
select PPTX when the request says `PowerPoint`, `deck`, `slides` or `.pptx`; select both when it says `both`
or `board pack`. Both formats must come from the same validated `report.json`.

```
python "${CLAUDE_PLUGIN_ROOT}/shared/qa_report.py" report.json --format <pdf|pptx|both> --out "Gradient Readiness Report - <Org>" --budget <this skill's directory>/references/layout-budget.json
```

This is the canonical delivery command: it renders, checks the layout budget and
creates the review artifacts. The readiness report is operational, not
analytical. It is exempt from the four-tile analytical-band labels, page-2 key
judgments, visual-before-table rule and `Analysis —` callout requirement. Keep
its established readiness tiles and diagnostic flow.

Meta: `eyebrow` "Platform Readiness", `header_label` "Readiness Review", `title` the organization name,
`subtitle` "Access, licensed capabilities and data coverage", `completeness` = capabilities available /
capabilities reviewed. `cover_facts`: Organization, Reviewed (date) only; the cover is a title page, so
readiness, access, licensing and check detail stay in the body. `signal.label` is a plain sentence, e.g.
"Ready to use, with some skills limited".

Signal: `ready` (connected, all core skills ready, no new failures) · `partial` (connected, but some skills
partial or not licensed, or degradable failures are present) · `not_ready` (not connected, auth failed, or any
core skill not available).

Sections (soft target 4–5 pages; hard ceiling 7):

1. **Summary** (`id: executive`) — bottom line in 3 sentences; tiles: Skills ready, Partly available,
   Not licensed, Checks passed.
2. **Skills you can use** — show Core, Blocked, and Paused status first, then
   runtime readiness for Core skills. Use full-width tables. Do not pair them in `two_col`; three columns
   are too narrow side by side. Each uses Skill, What it produces, and Note;
   status is explicit in the table title or a chip when needed. For the IC memo,
   show Portfolio Analytics core readiness and `Strategy Lab supplement: <Ready
   / Not licensed (optional) / Unavailable (optional)>` separately. A missing
   Strategy Lab supplement makes the IC memo Partly available, not Not licensed.
3. **Access and data** — `coverage` block for data domains; kv block for organization, role, licensed modules,
   roster capacity, and availability of the first portfolio's five opt-in exposure sections.
4. **Connection checks** — kicker gives the pass count as a sentence; table: Check, Tool, Result (chip), As of,
   Note with `widths` `["16%","28%","12%","12%","32%"]` and `nowrap: [3]`. Then a `findings` block listing
   new failures only (severity high when a core skill is blocked, medium otherwise).
5. **Try next** — `questions` block with 3 prompts tailored to what is ready,
   e.g. "Review our total portfolio", "Build a fixed-income sleeve allocation",
   and "Build the macro briefing deck for Thursday's committee".
6. **Appendix A — Sources and methods** (`num: "A"`) — tool, as-of, validation status, payload digest for each call.

Then follow "Check and deliver" in `${CLAUDE_PLUGIN_ROOT}/shared/report-style.md`. Apply the
canonical QA command's specific repair levers and rerun it until clean.

## 6. Offer next steps
- Do not offer Paused or Blocked workflows as runnable.
- If something is not licensed, say which module unlocks it; do not upsell beyond that.
