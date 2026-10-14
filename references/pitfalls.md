# Data pitfalls (generic patterns)

Model-specific versions with real names live in the unpublished pack (`../../../private/pitfalls.md`). These are the patterns to look for in any model.

- **Same column name, different meaning.** An id column (e.g. a partner id) can mean different things in different models, or be numeric in one and a string in another. Never join or compare across models on it without checking with `describe_model` and `sample_field`.
- **Minor units.** Money may be stored in minor units (cents). Cross-check one value against a known total before trusting a unit. Group by currency; never add currencies. Prefer a ready USD column for totals.
- **A "USD" column that is not turnover.** A converted amount column may use a different base than the bets. Reconcile it with a second model before ranking by it.
- **Sentinel dates.** A "no value yet" timestamp may be stored as 1970-01-01 instead of NULL. Filter on "greater than 2000-01-01" for "has happened". A boolean derived from such a column can also be false for "never".
- **Duplicates.** Customer-day rows can repeat. Count people with a distinct-count measure, never with the row count.
- **Cumulative and state columns** (lifetime totals, balances, recency, level): valid for one day only. Never sum them over days or currencies. They have no measure by design; keep it that way.
- **Snapshot tables.** A table of wallets or levels may hold every entity for every day (large scans) or only entities with a record that day (not the whole base). Check the row count per day before drawing conclusions, and always filter one date.
- **Different date fields and windows.** Every model has its own date field and rolling window. Align the period and field before comparing models. A request wider than the window just returns what exists; detect it from the first returned date and say so.
- **Cohort models.** Costs and same-day flags belong to the registration date, not to the cash date. Young cohorts are incomplete.
- **Lagging sources.** Some sources (e.g. risk or fraud signals) fill with a delay of days. Never compute a share for the last week of such data; use the last mature week and say which dates.
- **Restated history.** Some figures change after the fact (late records, payouts, statuses). Compare history with a tolerance, not equality.
- **Dirty text dimensions.** Trailing spaces and mixed case. After `sample_field`, use every variant with `in`, or `starts_with` / `contains`.
- **Booleans over several overlapping flags.** A customer can carry several flags: totals per flag do not add up to the customer count.
- **One-off or hard-coded models.** A model with a fixed start date and no end date keeps growing. Don't reuse it for other periods.
- **Small groups.** No automatic masking. Flag segments with fewer than ~30 players or attempts as unstable.
- **Weekly granularity.** Renta weeks start on Sunday; the first and last weeks of a range are partial. For Monday-to-Sunday weeks query days and group yourself.
- **Expensive scans.** `sample_field` on a large snapshot model can scan hundreds of MB. Prefer `describe_model` and a date-filtered `run_query`.
- **Data that models usually lack:** per-bonus balances, support tickets/chats, KYC status, responsible-gambling limits, odds and markets, CRM sends, PSP fees, chargebacks. Say "no data in the Renta models (nothing else checked)".
