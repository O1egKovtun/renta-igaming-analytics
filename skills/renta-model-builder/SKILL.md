---
name: renta-model-builder
description: Designs new or improved Renta data models for a Context Layer — turns a business question into model SQL over the data warehouse, checks columns and scan cost with dry_run, proposes which columns get SUM/AVG/DISTINCT measures, adds pre-computed metric columns (e.g. GGR), and writes model and column descriptions for Renta Metadata and dbt schema.yml from the metric statuses in the visuals skill's metrics_registry.json and the pack's private/metrics_map.md. Use when someone asks for a new model, "зроби модель", "макет моделі", "додай колонку GGR", "чому Claude не може це порахувати", "описи моделей", "metadata для Renta", "schema.yml", or when a question can't be answered because no model has the needed data or measure. Also read-only checks of sources, pipelines, failed runs, tracking-plan data quality and Customer 360: "pipeline", "source", "connector", "data quality", "tracking plan", "customer 360".
---

# Renta model builder

Goal: models that let Claude answer questions with one query, with metrics computed once (dbt, pre-computed metrics, descriptions in Models).

## Workflow

```
- [ ] 1. State the questions the model must answer (3–5), and the grain: one row = ?
- [ ] 2. Check existing models first (`list_models`, and the pack's private/models.md if it exists). Prefer adding a column to an existing model over a new one.
- [ ] 3. Draft SQL (one read-only SELECT ≤ 50 000 chars, no `;`)
- [ ] 4. manage_data_models dry_run on the source → columns + bytes; must be < 10 GiB
- [ ] 5. Measures plan per column
- [ ] 6. Descriptions (model + non-obvious columns)
- [ ] 7. Hand over: SQL, measures table, descriptions, test questions with expected numbers
```

## SQL rules

- Always add a date window on the partition/date column: `WHERE <date> >= DATE_SUB(CURRENT_DATE(), INTERVAL N DAY)`. Some tables require a partition filter.
- Put **metric logic in SQL** so Claude doesn't have to do arithmetic it can't order by. Examples:
  - `<real casino bets> - <real casino wins> AS casino_real_ggr`
  - the total GGR candidate (real + bonus, casino + sport) as one column
  - `DATE(<first deposit time>) = <registration date> AS is_ftd_same_day`
  - `NULLIF(<time column>, TIMESTAMP '1970-01-01')` to turn a sentinel date into NULL
- Clean dirty dimensions at the source: `TRIM(<region>)`, `LOWER(TRIM(<method>))`.
- Money: one currency per column. Prefer USD columns. If a column is local minor units, convert it (`/100`, except CLP) or name it `_minor_local`.
- Sources: `manage_data_models` `sources` lists them. The source can't be changed after creation.
- In dbt (preferred long-term): the same SELECT becomes `models/core/<name>.sql`. Renta then uses `model_type: dbt` or a table/view over the dbt output.

## Measures plan

Renta auto-enables SUM on every numeric column, so list what to switch OFF:

| Column kind | Measures |
|---|---|
| Additive money/counts per row | SUM |
| Ids | DISTINCT only |
| Cumulative / snapshot / balance / recency / rates | none (dimension), or AVG for rates |
| Durations | MEDIAN, P95 (AVG optional) |
| Flags, dates, text | none (dimensions / filters) |

## Descriptions (Renta Metadata = dbt schema.yml)

- Model description (≤600 chars): one row = …; date field and window (UTC); currency; what not to sum; what it is NOT for; related models.
- Column descriptions only for non-obvious columns: cumulative, units, flags (exact meaning), sentinels, "to confirm: …" where unknown.
- Metric wording matches the model description already in Renta, word for word. Output both a Renta paste block and a dbt block:
  ```yaml
  models:
    - name: <model>
      description: "<same text>"
      columns:
        - name: <col>
          description: "<same text>"
  ```
- Don't use Renta "Auto-generate with AI" on sensitive models: it reads sample values.

## Hand-over

If a draft of descriptions exists in the unpublished pack (`../../private/schema_draft.yml`), reuse and extend it instead of writing from scratch.

The person who manages Renta applies the change in the UI (Query, Measures, Metadata, Access tabs) or merges the dbt PR. After that:
- run `manage_data_models get` to confirm `updated_at` and the measures;
- run the test questions;
- add the new expected numbers to the reference queries in the unpublished pack (`../../private/golden_queries/`).

## Known improvements

The list of concrete models and columns to improve is company-specific and lives in the unpublished pack (`../../private/`), together with draft descriptions (`schema_draft.yml`).

## Sources, pipelines, data quality, Customer 360

Read-only checks only. Read [references/platform-tools.md](references/platform-tools.md) first: it lists the allowed calls, the health-check flow, and the strict rules for people-level Customer 360 data.
