---
description: Daily briefing from Renta: the last full day vs the same weekday last week, anomalies and stale models, as a dashboard
argument-hint: [YYYY-MM-DD] [region]
---

Build the daily briefing for: $ARGUMENTS (default: the last full UTC day, all regions).

Follow `${CLAUDE_PLUGIN_ROOT}/references/rules.md` and the renta-visuals skill. Read-only. Never print contact data.

1. **Models.** Take the model catalog from the pack's `private/models.md` if it exists, otherwise `list_models` and `describe_model`. Check `${CLAUDE_PLUGIN_ROOT}/skills/renta-visuals/references/model_limits.md` (and the pack's `private/model_limits.md`) for windows, units and currencies.
2. **Series.** For each metric below, one daily series for the 35 full UTC days ending on the briefing date (a daily series, not a total):
   - deposits (amount), deposit count, FTD, new players, withdrawals (amount): the player-activity model;
   - deposit success rate: the payments model, daily counts by status for deposits; success rate = successful / all attempts, divided by you, one value per day.
   If a model lacks the measure, skip the metric and say so. Do not substitute a different column.
3. **Freshness.** For every model used, query its date column ordered descending with limit 1 (within the last 14 days) to get its latest date.
4. **Analyse.** Write the input JSON (`{"as_of", "metrics": [{"name","unit","dates","values"}], "freshness": [{"model","max_date"}]}`) to a temp file and run
   `python3 -I "${CLAUDE_PLUGIN_ROOT}/scripts/anomalies.py" <file> --format json`.
   Only the script decides what is an anomaly; do not add your own thresholds. Do not explain a cause that the data does not show.
5. **Dashboard.** Build it with `${CLAUDE_PLUGIN_ROOT}/skills/renta-visuals/scripts/build_report.py` as `python3 -I <build_report.py> report.json reports/<YYYY-MM-DD>-brief.html` (artifact in claude.ai or Desktop):
   - one KPI tile per metric: value of the briefing day, `delta_pct` = `vs_last_week_pct`, `metric` key from `references/metrics_registry.json`;
   - `alerts`: one line per flagged metric (level `warn`) and per stale model (level `bad`), in the user's language;
   - two or three 14-day line charts (never mix units or magnitudes on one chart);
   - `notes`: model, period (UTC), currency, preliminary days.
6. **Reply** in the user's language: the path, the flagged metrics first (or "no anomalies"), stale models, one suggested next step such as `/renta-why <metric> <date>` for each flag.
