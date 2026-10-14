---
name: renta-visuals
description: Turns Renta query results into charts, KPI dashboards and diagrams for an iGaming operator — daily trends, provider comparisons, cohort funnels, region splits, top-N bars, department dashboards, data-flow and model diagrams (Mermaid). Use whenever the user asks for a chart, graph, dashboard, visual report, "графік", "діаграма", "дашборд", "візуалізуй", "покажи динаміку", "gráfico", or when an answer has a time series or more than ~6 comparable numbers that read better as a picture. Works with renta-querying for the data.
---

# Visuals for Renta data

Data first: get numbers with renta-querying (exact model, period, filters). Charts never show numbers you didn't query.

## Pick the form

| Question shape | Chart |
|---|---|
| Trend over days/weeks | `line` (one series per metric; ≤4 series) |
| Compare categories (providers, regions, partners) | `bar`, `horizontal: true` if labels are long; sorted desc; top-N + "others" |
| Composition at one point (≤6 parts) | `doughnut`; otherwise a stacked bar |
| Composition over time | `bar` with `stacked: true` |
| Funnel (registration → FTD → repeat deposit) | horizontal `bar`, stages in order, show the % of the first stage in labels |
| Two metrics with different units | two charts side by side, never a dual axis |
| Single numbers | KPI tiles with `delta_pct` vs the comparable previous period |

## Dashboard template

[assets/dashboard.html](assets/dashboard.html) is a self-contained page (Chart.js from cdnjs, light/dark, mobile). Copy it and replace only the `REPORT` object:
```js
{ title, subtitle: "<period> (UTC) · <model> · <currency>",
  kpis: [{label, value, unit, delta_pct, note}],
  charts: [{type: "line"|"bar"|"doughnut", title, unit, labels: [...], series: [{name, data: [...]}], stacked, horizontal}],
  notes: ["source, preliminary days, candidate formulas"] }
```
Where it goes:
- **claude.ai / Desktop:** publish it as an HTML artifact.
- **Claude Code:** write `reports/<YYYY-MM-DD>-<slug>.html` in the current project and give the path.
- **Slack:** scheduled posts can't attach HTML. Post the text summary; the dashboard link goes in if one exists.

## On-demand dashboard (`/renta-dashboard <metric> [period] [breakdown]`)

For any model and metric. The command is [commands/renta-dashboard.md](../../commands/renta-dashboard.md); this is the algorithm.

1. **Find it.** `list_models`, then `describe_model`: the model, the time dimension and the measures. A metric from igaming-metrics/references/metrics.md uses its formula; unapproved ones are labelled "candidate" with components.
2. **Check the limits** in [references/model_limits.md](references/model_limits.md) (and the pack's `../../private/model_limits.md` if it exists) before any query: window, cumulative/state columns, units, row limit, PII. Trim or refuse, and say so in `notes`. Never invent a period the model doesn't have.
3. **Query** read-only: a daily series (weekly if the period is over ~120 days) plus the comparable previous period; a breakdown as a separate top-N query. Divide ratios yourself.
4. **Build.** Write the report JSON and run `python3 -I scripts/build_report.py report.json reports/<YYYY-MM-DD>-<slug>.html`. The script checks that every series matches its labels. Without Python, copy the template and replace `REPORT` by hand.
5. **Reply** with the path, 3–5 findings, caveats. Findings come from the queried numbers only; a cause you can't see in the data is a question, not a statement.

Ambiguous metric (e.g. "activity")? Take the most likely reading, state it, continue. A metric with no measure and no formula: show its components, label "not approved".

## Rules

- Title says what and when. The subtitle carries period (UTC), model, currency. Units are in the chart title.
- Preliminary days (today, the last 1–2 days) go in `notes`; on line charts add "(prelim.)" to that label.
- Candidate or ✎ metrics are labelled in the title: "GGR (candidate)".
- Bars start at zero. Don't connect missing days. Sort categories by value unless the order is natural (dates, funnel stages).
- Never mix currencies in one series. Per-currency data → one chart per currency, or USD only.
- Very different magnitudes (e.g. deposits vs GGR) → two line charts, not one. Negative parts (bonus GGR) → separate bars, not a stacked bar.
- `unit: ""` for counts; `note` is a free string (e.g. "real <x> · bonus <y>"); `delta_pct` is a number. Empty category labels → "not specified".
- Keep it to ≤4 series per line chart and ≤10 bars; group the rest into "others".

## Diagrams (Mermaid)

For processes and structure (not numbers), use Mermaid. It renders in claude.ai, GitHub and Obsidian:
- data flow: `flowchart LR` BigQuery → Renta model → Claude → Slack
- funnel logic, model map (which model answers which question), release schedule (`gantt`)

Keep nodes ≤12 and label the arrows with what moves (e.g. "customer_id, daily").

## Department dashboard layouts

| Dashboard | KPI tiles | Charts |
|---|---|---|
| Executive daily | deposits, FTD, new players, GGR candidate, withdrawals (each vs the same weekday last week) | 14-day line of deposits and GGR; bar of deposits by region |
| Payments health | success rate, attempts, USD volume, P95 time | bar of success rate by provider (top-8); line of daily success rate for the top-3 providers |
| Marketing cohorts | registrations, same-day FTD, conversion %, affiliate payout | stacked bar of costs by type per week; bar of FTD by partner (top-10) |
| Risk | flagged FTD share, flagged count | bar of customers per signal flag; line of the weekly flagged share |
| CRM/VIP | active players, depositors, VIP customers | bar of customers by VIP level; line of DAU over 30 days |
