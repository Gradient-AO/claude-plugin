# Writing Standards for IC Memos

Committee members read the first page and skim the rest. Write so that someone who reads only Section 1 and
the Section 4 summary knows what is being asked, why, and what could go wrong.

## Principles

1. **Bottom line up front.** The recommendation and the vote requested come before any analysis.
2. **One claim, one source.** Every factual sentence carries a `[S#]` or `[Calc C#]` tag. If a claim has no
   source, delete it.
3. **Facts before judgment.** In each section, show the data first (tables), then at most three sentences of
   interpretation labeled as such where helpful ("Interpretation:").
4. **Show the downside.** Every recommendation names its key risks, the worst stress-test result, and the
   liquidity coverage after the change.
5. **Name the alternative.** Section 13 always includes at least one alternative considered and why it was not
   preferred (including "no change").
6. **Say what you don't know.** Every unavailable input appears as an open item with an owner and timing.
7. **Consistency over flair.** Use the template's status words, rating words and number formats every time,
   so memos can be compared quarter to quarter.

## Tone

- Plain, neutral, precise. Third person ("The portfolio…", "The Committee is asked…").
- Short sentences; one idea each. No rhetorical questions.
- Audience = Client: same structure; replace jargon in prose with plain terms on first use (for example
  "CVaR (expected loss in the worst 5% of years)"). Tables stay unchanged.

## Banned or restricted phrasing

| Avoid | Use instead |
|---|---|
| "will return", "expected to deliver" (as a promise) | "is assumed to return", "the CMA assumption is" |
| "guaranteed", "safe", "risk-free" (except the risk-free rate) | describe the specific risk level |
| "verified returns" | "GIPS-verified firm" only if the verification covers it; see GIPS skill |
| "outperform" without a period and benchmark | "+35 bps vs the policy benchmark over 1Y" |
| "significant" without a number | the number |
| "the Committee has approved" | "the Committee is asked to approve" |
| "our holdings" for illustrative data | "the illustrative portfolio" |

## Section-specific guidance

- **Section 1:** The recommendation sentence must contain the action, the size (weight, bps, or currency) and
  the subject. Example: "Reduce public equity by 300 bps to 47.0% and add 300 bps to private credit."
- **Section 2:** Exactly five bullets; each starts with its fixed bold label.
- **Section 5:** State the return basis (net or gross) once per table. Attribution commentary names the single
  largest effect and its sign.
- **Section 7:** Always show Gradient's figures next to the consensus check; if the gap for a held asset class
  exceeds 150 bps, mention it in prose and add it to Section 14 as a model risk.
- **Section 9:** Lead with the coverage ratio in both cases. If stress coverage is below 1.00, it is a High
  risk in Section 14.
- **Section 10:** Report diligence facts; do not characterize a manager's skill.
- **Section 14:** Each risk has a concrete mitigant (a limit, a monitoring trigger, a phased implementation),
  not "monitor closely".
