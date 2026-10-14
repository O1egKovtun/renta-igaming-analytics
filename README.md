# renta-igaming-analytics: Claude skills for iGaming analytics through Renta

🇺🇦 Українська версія: [README.uk.md](README.uk.md)

**Version:** 0.5.0 · **Content:** instructions, scripts and metric statuses only. No company data (no figures, ids, provider or partner names, model schemas).

## What it is

A Claude plugin: 2 skills, 5 commands and 3 scripts for the **Renta Context Layer** (MCP). Metric definitions, column meanings and data traps belong in the Renta Metadata descriptions of the models, not here. The plugin adds what metadata cannot: deterministic calculations (anomalies, change decomposition, regression checks), dashboards, shared query rules (`references/rules.md`), and a prompt for an unattended daily briefing (`routines/daily-brief.md`).

```mermaid
flowchart LR
  W[(Data warehouse)] -->|model SQL| R[Renta Context Layer]
  R -->|MCP tools| C[Claude]
  S[[This plugin]] -->|rules, scripts, templates| C
  C --> O[Answers, HTML dashboards]
```

## What's inside

| Skill | Purpose |
|---|---|
| `renta-visuals` | Chart selection, dashboard template, `build_report.py`, Mermaid diagrams, on-demand dashboard algorithm |
| `renta-model-builder` | Read-only checks of sources, pipelines, failed runs, tracking-plan quality and Customer 360 (`references/platform-tools.md`); Designs model SQL, measures plan and descriptions (dbt `schema.yml` / Renta Metadata) |

Commands (`/renta-igaming-analytics:<name>`):

| Command | What it does |
|---|---|
| `renta-brief [date] [region]` | Daily briefing: the last full day vs the same weekday last week, anomalies (`scripts/anomalies.py`, robust z-score) and stale models, as a dashboard |
| `renta-why <metric> [date] [by dimension]` | Splits a change across a dimension (`scripts/why.py`); ratios are split into rate and mix effects |
| `renta-dashboard <metric> [period] [breakdown]` | HTML dashboard for any model and metric; checks window, cumulative columns, units, row limits and PII first |
| `renta-check [golden.json]` | Re-runs reference queries and reports drift (`scripts/check.py`), to catch silent changes in models |
| `renta-start` | Short menu with example requests |

Dashboards support tabs (`tab` on a chart), alert lines (`alerts`), status badges taken from `references/metrics_registry.json` (`metric` key; unapproved metrics get a "candidate" or "not approved" badge), print to PDF and localized labels (`labels`). A local override file named by `RENTA_METRICS_STATUS` (`{"ggr": "approved"}`) changes a status in one place.

## Rules baked into the commands (`references/rules.md`)

- Renta is **read-only** (`context_layer`, and `manage_data_models` list/get/schema). No create, update or delete, even if the user "confirms".
- Contacts, names, documents, cards, IPs and device ids are never shown. Player ids and aggregates are allowed.
- Never invent a formula: show the components and label "candidate / not approved".
- Never sum cumulative columns over days or currencies; count people with distinct-count measures.
- State model, period (UTC), filters and currency with every number; mark preliminary days.

## Local knowledge pack (optional, not published)

Company-specific facts (model catalog, windows, units, partner and provider names, verified reference numbers, approval status of formulas, tests) belong in a local `private/` folder at the plugin root. It is in `.gitignore` and not packaged by `build.sh`. Commands read `private/models.md`, `private/model_limits.md` and `private/golden.json` when they exist; without them, Claude discovers models with `list_models`, `describe_model` and `sample_field` and treats nothing as pre-verified.

## Install

- **Try locally:** `claude --plugin-dir /path/to/this/repo`
- **From a marketplace:** `/plugin marketplace add <owner>/<repo>`, then `/plugin install renta-igaming-analytics@<marketplace>`
- **claude.ai:** `./build.sh` builds one zip per skill in `dist/` (only the two remaining skills; the query and personal-data rules are not inside them, so put the block from the unpublished `private/project_instructions.md` into the claude.ai project instructions). Upload under Organization settings → Skills.
- **Prerequisite:** the Renta connector enabled in Claude.

## Before publishing

Run `./leak_check.sh`. It scans the public tree for terms listed in `private/leak_terms.txt` (one regex per line, kept out of the repo) and for number patterns that look like business figures. It must print `clean`.

## Maintenance

| Change | Update |
|---|---|
| A formula was approved | the mapping and status in `private/metrics_map.md`, the description in Renta Metadata, and `skills/renta-visuals/references/metrics_registry.json` |
| A Renta model changed | `private/models.md` and `private/golden_queries/` |
| A new data trap | the column or model description in Renta Metadata (draft in `private/schema_draft.yml`) |
| Any skill change | test it, then `./build.sh` |
| Any script or template change | `python3 tests/test_scripts.py` and `python3 tests/test_stress.py`, then `./leak_check.sh` |
