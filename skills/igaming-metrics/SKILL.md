---
name: igaming-metrics
description: The single source of metric definitions for iGaming analytics — FTD, new players, depositors, active players, deposits, withdrawals, net deposit, GGR, NGR, bonus GGR, hold/margin, RTP, ARPU, conversion, CPA, ROMI, retention, payment success rate — with how each is calculated and whether it is approved. Use whenever a user asks to calculate, compare or explain any business metric, or uses synonyms in Ukrainian, Russian, Spanish or Portuguese (депозити, депы, депозитов, depósitos, ganancia bruta, primer depósito, cadastros). Pair with renta-querying for how to run the queries.
---

# iGaming metric dictionary

Every metric has exactly one definition, found in [references/metrics.md](references/metrics.md). Local approval status and the mapping to model measures live in the unpublished knowledge pack `../../private/metrics_map.md`; read it first when it exists. Synonyms in UK/RU/ES/PT map to metric names in [references/glossary.md](references/glossary.md).

## How to use

1. Map the user's words to a metric via the glossary. If two metrics fit ("revenue" could be GGR, NGR or deposits), ask one short clarifying question.
2. Look up the metric's **status**:
   - **approved:** compute it exactly as written.
   - **working:** compute it, and add "(working definition, not approved)".
   - **not defined:** do NOT invent a formula. Show the components (e.g. bets and wins separately) and say: "the {name} formula is not approved; here are the components". If a **candidate** formula is listed, you may compute it, labelled "candidate".
3. Find the model and measures (the pack's mapping, or `describe_model`) and run them (renta-querying workflow). For ratios, show numerator and denominator.
4. State what's included: real vs bonus money, casino vs sport, which statuses, which currency.

## Universal rules

- Never mix currencies. Never sum cumulative columns across days.
- "Active", "churned" and "retained" depend on an activity definition that may not exist. Until it is filled in, report distributions (e.g. by recency) instead of labels.
- A metric that needs two models (e.g. CPA = costs ÷ FTD) means two queries over the same period and date logic, with any mismatch called out.
- If the metric isn't in metrics.md, say so and propose a definition for a human to approve. Don't use it as fact.

## Changing definitions

Definitions change only when the owner approves. The editor updates metrics.md and, in the pack, the mapping and status; every other skill references this one, so nothing else needs editing.
