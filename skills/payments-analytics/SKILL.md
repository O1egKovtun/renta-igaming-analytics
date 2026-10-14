---
name: payments-analytics
description: Analyzes deposit and withdrawal payments for an iGaming operator via Renta — payment success/approval rate by provider, attempts vs successful vs pending, successful volume in USD, processing time median/P95, withdrawals, provider drops. Use for questions from the payments team or anyone asking which PSP/provider fails, "успішність платежів", "апрув по провайдерам", "tasa de aprobación", "processing time", "де падають депозити", payment_id lookups. Builds on renta-querying and igaming-metrics.
---

# Payments analytics

Follow renta-querying for the workflow and data policy, and igaming-metrics for definitions. Model and column names, known values and verified numbers are in the unpublished pack (`../../private/`); without it, discover them with `list_models`, `describe_model` and `sample_field`.

## Workflow

1. Learn the real values of `type` (deposit/withdrawal) and `status` (success/failed/pending…) with `sample_field`; don't assume.
2. Deposits and withdrawals are separate: always filter the type.
3. Success rate = successful ÷ (successful + failed + pending), with all three counts shown. Then add a second rate that leaves pending out of the denominator.
4. Money comes only from the ready USD amount measure. A local-currency amount is used only when grouped by currency (and may be in minor units).
5. Processing time: median and P95 per provider and slice. Never average percentiles across days or providers.
6. **The provider (PSP) and the partner/affiliate id are different columns.** Never use a partner id as the provider.
7. Payment-method values are often dirty (trailing spaces, mixed case). Filter with `contains` / `starts_with`.
8. The unit of processing time may be undocumented. Say "unit not confirmed".

## Interpreting

- Empty or NULL provider: exclude it from the top-N and show it as a separate line.
- If pending = 0 in the period, say so explicitly. Then success rate = success ÷ (success + failed).
- An average amount per provider far off the others: flag it as an anomaly to check, don't explain it.
- Providers with fewer than ~100 attempts in the period: mark them "small sample"; for alerts ignore providers below ~1000 attempts a day and list them as a side note only if the drop is large.
- The last 1–2 days have pending statuses that will resolve, so they're preliminary.
- A drop in success rate: compare the same weekdays, and check whether the attempt mix moved between providers before blaming one.
- Reconciliation: successful deposit counts in payments vs deposit counts in the player-activity model for the same day should be close. Report the gap rather than hiding it.

Allowed: payment and customer ids in lists (e.g. "the 20 slowest withdrawals"). Never card numbers or payment details.
