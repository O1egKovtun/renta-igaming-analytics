# Metric definitions (standard, company-neutral)

These are the standard iGaming definitions. Which of them the company has **approved**, which model and measure implements each one, and who owns the undefined ones are recorded in the local knowledge pack (`../../../private/metrics_map.md`) when it exists. Status words: **approved** (signed off), **working** (in use, not signed off), **not defined** (do not invent a formula), **candidate** (may compute, label "candidate").

If the pack is absent, treat GGR, NGR, ARPU, ARPPU, CPA, ROMI, "active player", retention, churn and bonus abuse as **not approved**: compute only the candidate formula given here, label it, and show the components.

## 1. Players and funnel
| Metric | Definition |
|---|---|
| New players / registrations | accounts created in the period (registration day flag, or the create time of the customer table). Both should match; if they don't, report the gap |
| FTD | players whose first deposit falls in the period |
| Depositors | players with at least one deposit in the period |
| Active players | **not defined by default** (bet, deposit or login?). Until the owner defines it, report "players with activity" and a distribution, not "active" |
| Reg to FTD conversion | FTD ÷ registrations over the same period (two queries). For cohorts, state whether FTD is same-day or at any time |
| Cohort FTD at any time | cohort members whose first deposit exists to date (exclude the "no deposit" sentinel date) |
| Same-day FTD conversion | cohort members who deposited on the registration day ÷ cohort registrations |

## 2. Money in and out
| Metric | Definition |
|---|---|
| Deposits (amount, count) | successful deposits |
| Withdrawals (amount, count) | paid-out withdrawals |
| Net deposit | deposits − withdrawals |
| Average deposit | deposit amount ÷ deposit count for the period (never an "average deposit" column that is cumulative) |

## 3. Gaming revenue

**Column convention.** Check whether the bet and win columns include bonus money. Do not assume. If it is unconfirmed, state the assumption once: real-money columns and bonus columns are separate and additive; never subtract bonus from real. Real turnover = real bets; total turnover = real + bonus.

| Metric | Definition |
|---|---|
| Real GGR (casino, sport) | real bets − real wins, per product |
| Bonus GGR | bonus bets − bonus wins, per product |
| **GGR (candidate)** | (real bets + bonus bets) − (real wins + bonus wins), casino + sport. Always report with the real/bonus and casino/sport split. Label "candidate, formula not approved" unless the pack says it is approved |
| NGR | not defined by default; typically GGR − bonus cost (− taxes, fees, chargebacks). Show components, never a total |
| Hold / margin | GGR ÷ bets, per product; state whether bonus is included. One day of sportsbook margin is noise: use 7+ days |
| RTP (casino) | wins ÷ bets, in one currency or as a unit-free ratio |
| ARPU, ARPPU | revenue base ÷ players or depositors; **not defined** until the revenue base (GGR or NGR) is approved |
| Bonus and cashback given | sums of bonus, accepted bonus and cashback amounts |

Per-player rankings:
- If a ready difference column exists (e.g. bonus GGR), order by it directly.
- Otherwise the query tool cannot order by an expression: query the player id with the bet and win measures, order by bets descending with a generous limit (≥500), compute the difference per row, sort, and say the ranking is within the returned rows.

## 4. Payments
| Metric | Definition |
|---|---|
| Attempts | all payment orders of a type (deposit or withdrawal), counted by distinct payment id |
| Success rate | successful ÷ (successful + failed + pending), per provider; show the three counts; add the rate without pending when pending is non-zero |
| Successful volume | sum of the USD amount column over successful payments |
| Processing time | median and P95 per slice; never average percentiles |

## 5. Marketing
| Metric | Definition |
|---|---|
| Cost by type | each cost type (affiliate, social, listing fee, revenue share, affiliate-network payout) shown separately |
| Total cost | not defined by default (which types?). Show components |
| CPA | total cost ÷ FTD (same-day or at any time); **not defined** until both are approved. Show cost per type per FTD |
| ROMI | (revenue − cost) ÷ cost over a cohort window; **not defined**; needs an approved revenue metric and window |

## 6. Retention and CRM
| Metric | Definition |
|---|---|
| Retention Dn | share of a registration cohort active on day n; depends on the activity definition |
| Churned / reactivated | no activity for N days / active after N inactive days; N not defined by default |
| VIP distribution | customers per VIP level on one day (a state, never summed over days) |

## 7. Risk
| Metric | Definition |
|---|---|
| Share of FTD with a multiaccount signal | flagged FTD customers ÷ all FTD customers over the same period (two queries). State coverage; mature days only (the signal source lags) |
| Signal groups | distinct hashes shared by more than one customer, only if hash columns exist; never print hashes |
| Bonus abuse | not defined |
