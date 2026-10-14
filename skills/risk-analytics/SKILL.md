---
name: risk-analytics
description: Analyzes fraud, multiaccount and compliance-proxy signals for an iGaming operator via Renta — share of FTDs with multiaccount signals, signal types (common email/phone/personal id/click id/IP/device), signal groups, days between deposits and activity, large deposits, fast withdrawals, play intensity. Use for risk, antifraud, AML/compliance and bonus-abuse questions — "мультиакаунти", "дублі", "бонус-абʼюз", "підозрілі гравці", "multicuentas", "fraude". Builds on renta-querying and igaming-metrics.
---

# Risk analytics

Follow renta-querying for the workflow and data policy, and igaming-metrics for definitions. Model and column names, coverage and verified numbers are in the unpublished pack (`../../private/`); without it, discover them with `list_models` and `describe_model`.

Typical sources: a multiaccount-signals model (one row per flagged first-deposit player), the player-activity model (behaviour), and the customers model (status, block reasons).

## Hard rules

- Risk and customer models **may contain contact and document columns** (email, phone, names, passport/personal id, birth date, IP, device, click id). Never select, sample, filter or group by them. Use only the boolean signal flags, recency/day-difference columns, counts, partner id, region, dates, and the customer id.
- Signal flags overlap (shared phone, email, document, name+device, name+IP, click id). Totals per flag do not add up to the customer count.
- If hash columns exist: count group sizes only, never print hashes.
- A signal is not proof. Write "the signal matches criterion X", never "the player is a fraudster". Bans and payout decisions are made by a human.
- Customer-id lists are allowed for case review (default limit 50). Each row carries its signal flags, not personal data.

## Interpreting

- **"Has a multiaccount signal"** = the customer has a row in the signals model. Numerator: distinct flagged customers by first-deposit date. Denominator: distinct FTD customers from the player-activity model, same period (two queries).
- **The signal source usually lags.** Never compute a flagged share for the last ~7 days; use the last mature week and say which dates. A falling share in recent days is a data delay, not an improvement.
- Coverage is partial: always state it. No record ≠ clean.
- Strong vs weak link, bonus-abuse formula and group-size threshold are not defined by default. Report flag distributions and combinations without labelling.
- Compliance proxies (large deposits, fast withdrawals, intensity) need thresholds that are not defined. Start such answers with "proxy indicators, not a compliance status".
- There is normally no KYC status, ban outcome, card data or geolocation in the models.
