# Post spec format (Tactical Dashboard and Ask Gradient)

A spec is a JSON file Claude writes. **Words are typed; numbers are referenced.** `scripts/spec.py` resolves every reference from a saved Gradient payload, so no number on the image is ever typed by hand.

## Inputs
```json
"inputs": {"rr": "rr_2026-10-21.json", "cma": "cma_baseline.json", "grip": "grip.json", "regime": "regime.json"}
```
Paths are relative to the spec file. Any input with `validation.status` other than `passed` stops the render. Save each Gradient tool result to a file first (write inline results to JSON; copy values exactly, never round or retype).

## Value nodes
| Node | Example | Meaning |
|---|---|---|
| Reference | `{"ref": "rr:board_total[pair_id=growth_vs_value].relative_3m_pct", "fmt": "pct1"}` | Read from input `rr` at that path |
| Derived | `{"op": "sub", "args": [ref, ref], "scale": 100, "fmt": "pp1"}` | `sub`, `add`, `mul`, `div`; optional `scale` |
| Literal text | `{"text": "n/a"}` | Words only, never a number |

Path syntax: `a.b` keys, `[3]` list index, `[key=value]` first list item whose key equals the value.

Formats: `pct1`/`pct0` (value already in %, signed), `x100pct1`/`x100pct0` (decimal → %), `pp1` (percentage points), `int`, `num2`, `prob0` (decimal probability → %), `ord` (95 → 95th), `date` (ISO → Oct 21, 2026), `title` (CONTRACTION → Contraction), `text`. Add `"sign": false` to drop the leading +.

Mixed text: a list such as `[{"ref": "...", "fmt": "int"}, "-day · ", {"ref": "...", "fmt": "ord"}, " pctile"]` is joined with no extra spaces.

## Always run `--facts-only` first
It prints every resolved value with its location in the spec, plus each input's validation status, as-of dates and payload digest. Check that every number you use in the headline, analysis or post copy appears there (or in a cited source).

## Common fields
`as_of` (a date reference), `headline` (≤90 chars), `explain` (≤700), optional `explain_square` (shorter version for the square image), optional `watch` (≤200, "what would change our read"; portrait only unless `watch_on_square: true`), `source_line` (full sources for the footer), `post_question` (not drawn: the question asked in Claude, for the post text), optional `check_values` (not drawn: extra references so `--facts-only` checks numbers used in the analysis).

## Tactical Dashboard fields
`eyebrow` (optional), `subtitle`, `context` (up to 3 tiles: `label`, `value`, `detail` list, optional `value_color: "stance"` with a `stance` reference), `columns` (column headers), optional `col_widths` (label column first, fractions summing to 1), `rows` (≤8 comparison rows: `label`, `sublabel`, `cells` each with `value` or a computed `agree: [ref, ref]`, optional `note`, optional `color: "sign"|"none"`; optional `"square": false` to leave a row off the square, which holds 6; group headers are rows of the form `{"group": "Regions"}`), `footnotes` (1–2 short lines), `analysis_label` (optional).

## Ask Gradient fields
`slug` (file name), `eyebrow` (optional), `headline` (the answer, ≤90), `subtitle` (optional), `tiles` (up to 3: `label`, `value`, `detail`, optional `color: "accent"|"sign"`), optional `chart` (`title`, optional `value_label` and `value2_label`, `bars` ≤8: `label`, `value`, optional `value2`, optional `highlight: true`), `analysis_label` (optional).

## Worked examples
See `examples/` in this skill for the spec that produced the sample post.
