---
description: Explain a change in a metric by splitting it across a dimension (region, partner, provider, ...)
argument-hint: <metric> [date or period] [by dimension]
---

Explain the change in: $ARGUMENTS

Use renta-querying and igaming-metrics. Read-only. Never print contact data.

1. **Parse.** Metric, the period to explain (default: the last full UTC day) and the comparison period (default: the same weekday a week earlier; for a multi-day period, the preceding period of the same length). State both.
2. **Model and limits.** Find the model and measure (pack catalog or `list_models` / `describe_model`) and check `renta-visuals/references/model_limits.md` and the pack's `private/model_limits.md`. Skip cumulative or state columns. If the metric is not defined, show its components instead.
3. **Dimensions.** If the user named one, use it. Otherwise try the dimensions that exist in the model among region, partner, payment provider, game provider, product, currency, and keep the one with the highest `top_share_of_gross_pct` (additive) or the largest top effect (ratio). Never use contact or identification columns.
4. **Queries.** One query per period with the dimension, using a `between` filter for totals. Clean dirty text keys first (trailing spaces, case). For a ratio (success rate, conversion) query numerator and denominator.
5. **Decompose.** Write `{"metric","unit","kind":"additive"|"ratio","dimension","a_label","b_label","rows":[...]}` (a = the period being explained, b = the comparison; row shapes are in the script header) to a temp file and run
   `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/why.py" <file> --format json`.
6. **Reply** in the user's language: one sentence with the top contributors and their share, the table of the top 5, caveats (preliminary days, candidate metric, small sample). The decomposition says WHERE the change is, not WHY it happened: a cause the data does not show is a question for the owner, not a statement. If one key explains most of the change, suggest the next drill-down (for example that key by another dimension).
