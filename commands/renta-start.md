---
description: Short menu of what this plugin can do with Renta, with example requests
---

Show the user this menu in their language, then ask what they want to do. Keep it to the list; add nothing else.

**Ask in plain words** (the skills trigger by themselves): deposits, FTD, new players, payment success by provider, marketing cost by type, risk flags, VIP levels.

**Commands**
- `/renta-igaming-analytics:renta-brief [date] [region]`: daily briefing, yesterday vs the same weekday last week, anomalies and stale models.
- `/renta-igaming-analytics:renta-why <metric> [date] [by dimension]`: where a change comes from (region, partner, provider).
- `/renta-igaming-analytics:renta-dashboard <metric> [period] [breakdown]`: an HTML dashboard for any metric.
- `/renta-igaming-analytics:renta-check [golden.json]`: re-run the reference queries and report drift.

**Rules built in:** read-only Renta access, no contact data, UTC dates, unapproved formulas (GGR, NGR, CPA, ROMI, active player, ARPU, retention) shown as "candidate" with their components.

**Examples:** "deposits and FTD for yesterday", "why did registrations jump on the 7th", "success rate by provider for 30 days", "dashboard of player activity for last month".
