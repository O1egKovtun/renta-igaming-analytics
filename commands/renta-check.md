---
description: Re-run the golden (reference) queries and report which numbers drifted, to catch silent changes in Renta models
argument-hint: [path to golden.json]
---

Run the data regression check: $ARGUMENTS

Read-only. Use renta-querying.

1. **Golden file.** Use the given path; otherwise the first that exists: `private/golden.json` (the unpublished pack), `./renta-golden.json`. If none exists, say so, show the format below, and stop. Do not invent reference numbers.
   Format: `{"cases": [{"id", "label", "expected", "tolerance_pct", "date", "window_days", "query": {"model_id", "measures", "dimensions", "filters", "note"}}]}`. `expected` is a number the team has verified; `date` + `window_days` let the check skip a case whose date has left the model's rolling window.
2. **Run.** For every case whose date is still inside its window, run its `query` through `context_layer` (one call per case; run independent calls together) and extract the single number. A query that returns no row is `null`.
3. **Compare.** Write `{"<id>": number|null}` to a temp file and run
   `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/check.py" <golden> <results>`.
4. **Reply** in the user's language: the counts (ok, drift, missing, expired) and every drift with expected, actual and gap. A drift is a finding to investigate (a changed model, a restated source, a late-arriving day), not a reason to edit the golden file. Never update `expected` unless the user says the new number is verified.
