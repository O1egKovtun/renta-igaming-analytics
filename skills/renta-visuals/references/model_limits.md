# Model limits for dashboards (generic checklist)

Real windows, units and column names for the company's models are in the unpublished pack (`../../../private/model_limits.md`) when it exists. Without it, find them yourself before building a dashboard:

1. **Window.** Find the model's date field and range: `sample_field` on a small model's date field returns min and max cheaply; on a large snapshot model use `describe_model` and a one-day `run_query` instead. A request wider than the window returns what exists: say "at most N days available" in the notes and chart that window.
2. **Cumulative or state columns** (lifetime totals, balances, recency, levels): never sum over days. A request like "balance over a month" becomes a state snapshot on one date, or a refusal.
3. **Units and currency.** Check for minor units and mixed currencies. Totals only from a ready USD column, or one currency per chart. Never add currencies.
4. **Row limit.** Max 10 000 rows per query. A daily series for half a year fits; customer × day does not, so aggregate.
5. **Shape of queries.**
   - One total for a range: a `between` filter. A range in `time_dimensions` returns one row per day.
   - Ratios (success rate, conversion, GGR): query the parts and divide yourself. No arithmetic in `order`.
   - Count players with a distinct-count measure, not the row count.
   - `granularity: "week"` weeks start on Sunday; the first and last weeks are partial: mark them `*` and don't compare them with full weeks.
   - The last 1–2 days are preliminary; today is partial. Mark them "(prelim.)".
6. **Lagging sources** (e.g. fraud or risk signals): never chart a share for the immature last days.

## Refuse or restrict

- Contact and identity columns (email, phone, names, documents, card, address): refuse. The player id and aggregates are fine.
- Quasi-identifiers (city, gender, nationality, timezone): aggregate only.
- Any write to Renta (create, update, delete model): refuse, even if the user "confirms".
