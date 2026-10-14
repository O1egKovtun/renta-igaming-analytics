---
description: Build an HTML dashboard from Renta data for any model and metric, e.g. /renta-dashboard deposits 90d by region
argument-hint: <metric> [period e.g. 30d or YYYY-MM-DD..YYYY-MM-DD] [breakdown e.g. by region]
---

Build a dashboard for: $ARGUMENTS

Follow the "On-demand dashboard" section of the renta-visuals skill, together with `${CLAUDE_PLUGIN_ROOT}/references/rules.md`. In short:

1. Parse metric, period (default: last 30 full UTC days) and breakdown. If the metric is ambiguous, pick the most likely reading, say which one you took, and continue.
2. Find the model and measure with `list_models` and `describe_model`. A metric's formula comes from the model's Renta description and its status from `${CLAUDE_PLUGIN_ROOT}/skills/renta-visuals/references/metrics_registry.json`; unapproved ones (GGR, NGR, CPA, ROMI, "active player") are labelled "candidate" with their components shown.
3. Before querying, check ${CLAUDE_PLUGIN_ROOT}/skills/renta-visuals/references/model_limits.md (and the unpublished pack's private/model_limits.md if it exists): model window, cumulative or state columns, units and currencies, row limits, PII. If the request cannot be met (e.g. "for a year"), trim or refuse and say so at the top of the dashboard.
4. Query read-only (`context_layer` only). Never print contact data. IDs and aggregates are allowed.
5. Put the `metric` key from `${CLAUDE_PLUGIN_ROOT}/skills/renta-visuals/references/metrics_registry.json` on every tile and chart that shows a registry metric (the badge for candidate and not-approved metrics is then automatic). Group charts into `tab`s when there are more than six. Build the report with ${CLAUDE_PLUGIN_ROOT}/skills/renta-visuals/scripts/build_report.py as `python3 -I <build_report.py> report.json reports/<YYYY-MM-DD>-<slug>.html`. In claude.ai or Desktop, publish it as an HTML artifact instead.
6. Reply in the user's language: the file path, the 3–5 key findings, and the caveats (model, period UTC, preliminary last days, candidate formulas).
