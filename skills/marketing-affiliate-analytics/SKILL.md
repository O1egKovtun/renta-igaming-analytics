---
name: marketing-affiliate-analytics
description: Analyzes acquisition for an iGaming operator via Renta — cohort registrations, same-day FTD, reg→FTD conversion, marketing costs by type (affiliate, SMM, listing fee, revshare, affiliate-network payouts), partner/offer performance, CPA and ROMI components, registrations by region. Use for marketing/UA/affiliate questions — "витрати по партнерах", "CPA", "ROMI", "конверсія реєстрацій", "топ партнерів за FTD", "registros por país", offer_id, partner_id. Builds on renta-querying and igaming-metrics.
---

# Marketing and affiliate analytics

Follow renta-querying for the workflow and data policy, and igaming-metrics for definitions. Model and column names, region codes and verified numbers are in the unpublished pack (`../../private/`); without it, discover them with `list_models` and `describe_model`.

Typical sources: a registration-cohort model with costs, a customers model (registrations by create time and region), and the player-activity model (later revenue of cohorts).

## Rules

- **Cohort logic.** Costs and same-day FTD are attached to the registration date. This is not cash-period spend; say so when someone compares against invoices.
- Same-day FTD counts only deposits made on the registration day. **Cohort FTD to date** uses "first deposit time greater than 2000-01-01" because a "no deposit" sentinel date is often stored instead of NULL, so a false same-day flag also covers non-depositors. Say which FTD definition you used.
- Region codes can have dirty values (trailing spaces). Use `in` with every variant or `starts_with`. An empty region is shown as "not specified".
- Don't use columns with unclear meaning. Report a zero cost as zero, not as missing data.
- **Show cost types separately.** "Total cost", CPA and ROMI are not approved by default. Show the components and the per-FTD cost per type, never a silent total. The cost currency may be unconfirmed: say so.
- **Partner ids** can live in different id spaces in different models. For partner metrics use the marketing cohort model only, and don't compare partner counts between models.
- **Ranking:** partners or offers with fewer than ~20 FTD in the period → "unstable". Show top-N plus an "others" aggregate.
- **Registrations by region** come from the customers model's region column. Rarely filled columns (e.g. a country field) must not be grouped by. Its create time is a TIMESTAMP, so filter `gte`/`lt`. Never select its contact or name columns.
- **Period comparisons:** equal-length periods and aligned weekdays. Cohorts younger than 7 days are preliminary, and their same-day conversion is understated.
- Media-buy cost tables may be absent or stale; say so if asked.
