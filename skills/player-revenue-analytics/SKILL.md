---
name: player-revenue-analytics
description: Analyzes player activity and revenue for an iGaming operator via Renta — daily deposits/withdrawals, FTD, new and active players, casino and sport bets/wins, GGR and bonus GGR (candidate formulas), top players by GGR, cashback and bonus amounts, VIP levels, casino games and providers, retention and recency. Use for executive, finance, CRM, VIP, bonus, casino and sportsbook questions — "депозити вчора", "GGR за тиждень", "топ гравців", "bonus GGR", "VIP рівні", "hold по провайдерах", "ретеншн", customer_id lists. Builds on renta-querying and igaming-metrics.
---

# Player and revenue analytics

Follow renta-querying for the workflow and data policy, and igaming-metrics for definitions. Model names, columns, windows and verified numbers are in the unpublished pack (`../../private/`, see its README); without it, discover them with `list_models` and `describe_model`.

Typical sources: a player-by-day activity model (main), a VIP-level-by-day model, a game-by-player-by-day casino model, and possibly one-off models for a campaign or period.

## Rules

- **GGR is not approved by default.** Use the candidate formula from igaming-metrics. **Every GGR figure, including bonus GGR and top-N rankings, gets the label "candidate, formula not approved"** unless the pack says it is approved. Always split it out: casino vs sport, real vs bonus, bets and wins as separate columns.
- "GGR" without qualifiers = the total candidate (real + bonus, casino + sport). Show real GGR and bonus GGR as its parts.
- Sign: GGR = bets − wins = the operator's gain. "Max GGR player" = the largest positive value. If the user may mean the player's biggest win, state your reading in one line.
- Headcounts: the distinct-customer measure with no filter = all players with a row that day. Depositors, FTD and new players each need their own flag filter.
- **Top-N players** (allowed, by player id): if a ready difference column exists, order by it. Otherwise pull bets and wins with a generous limit (≥500) ordered by bets, compute the difference, sort, and say the ranking is within the returned rows. Show extra fields only if a column exists; per-bonus balances and "excess deducted" usually don't.
- **Cumulative columns** (lifetime totals, recency, balances) are one-day only. For recency distributions pick a single date.
- **Money:** confirm the unit and currency (reconcile with the payments model); count players with the distinct-count measure, never the row count.
- **VIP × revenue** needs two queries (levels, money) over the same date. Fix the level snapshot date, and say if the VIP model covers only players with a record that day.
- **Casino games:** amounts may be in local minor units per currency, so group by currency. A converted-USD bet column may not be turnover; check before ranking. Rank games and providers per currency or by unit-free RTP/hold; RTP and hold on small turnover are noise.
- **Sportsbook:** one day of margin is noise; use ≥7 days. There are normally no odds, events or markets in the data.
- **Retention, active, churn:** the activity definition may not exist; report distributions and state the assumption.
- Executive totals: ≤5 lines, with the same weekday last week as the comparison and a percent change.
