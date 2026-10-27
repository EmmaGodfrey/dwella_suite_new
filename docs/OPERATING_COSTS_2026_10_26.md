# Dwella operating cost worksheet

Prepared 2026-10-26 for pricing discussion. No subscription prices or provider
choices are activated by this document. These are planning estimates, not an
observed average from production usage or an all-inclusive supplier quote.

## Commercial direction

Claude's saved discussion records three paid tiers, plus a fourth per-unit tier
above a threshold, and no freemium. Prices, thresholds, included usage and billable
units remain undecided. User clarified on 2026-10-26: tenants bear collection fees,
landlords bear payout fees, and the product is moving away from automatic payouts.
This is business direction, not evidence that the running payout worker or fee
calculation has been changed. This worksheet supplies cost inputs; it does not
invent the missing tier details.

## Fixed monthly baseline

For illustration only, USD 1 = K20. Replace with the actual billed exchange rate,
including card conversion charges. At K25/USD the same $38 baseline is K950.

| Item | Monthly USD | Monthly ZMW at K20/USD | Status |
| --- | ---: | ---: | --- |
| Server | $18 | K360 | Current bill supplied by user |
| Handy assistant | ~$20 | ~K400 | User's anticipated price; confirm scope and usage cap |
| Existing Gmail SMTP | $0 incremental assumed | K0 incremental assumed | User uses a Google app password; any existing mailbox subscription is separate |
| Baseline including anticipated Handy | ~$38 | ~K760 | Excludes variable costs and the unpriced items below |

The present confirmed server bill alone is $18. Do not describe Handy's proposed
price as an already incurred bill. The server hosts the current database and
workers; do not add a hypothetical managed database/Redis subscription on top.

## Message costs

| Channel | Unit-cost input | Cost for 1,000 | Confidence / qualification |
| --- | ---: | ---: | --- |
| SMS to Zambia | K0.24 per segment | K240 | Africa's Talking published entry band; higher spending bands list K0.21/K0.19/K0.17 |
| WhatsApp utility reminder | K0.08 provisional Meta base benchmark | K80 provisional | $0.004 x K20; dated rate card, not a confirmed October 2026 quote; intermediary charges excluded |
| WhatsApp marketing | K0.45 provisional Meta base benchmark | K450 provisional | $0.0225 x K20; same dated-rate limitation; not interchangeable with utility reminders |
| Existing Gmail email | K0 incremental assumed | K0 incremental assumed | Sending limits apply; does not imply unlimited delivery |
| In-app notification | No external per-message tariff in current flow | No separate provider bill | Uses existing server/database resources |

SMS is billed in segments, not necessarily one charge for the whole text. Long
messages and Unicode can increase the segment count. Africa's Talking describes
160 characters for a standard single segment and 70 with special characters.
Confirm taxes, account eligibility, sender approval and final tariffs before
funding an account. No SMS/WhatsApp provider has been selected yet.

WhatsApp's current official page confirms pricing depends on recipient market
and message category. Its current downloadable regional rate card could not be
retrieved during this check. The accessible Meta rate card mirrored by Gupshup
is effective July 2025: Rest of Africa utility/authentication $0.004, marketing
$0.0225. These support a provisional benchmark, not a verified current Zambia
quote. Confirm Zambia mapping, approved template category, current account rate
and any provider markup before committing subscription allowances. Do not assume
all reminders qualify for a free conversation window.

Personal Gmail documents a daily limit around 500 emails; Workspace has different
limits. A monthly total alone is insufficient when all rent notices go out on the
same day. A paid transactional email service is an additional future cost.

## Illustrative usage and budgeting

Assume each occupied unit generates 2 single-segment SMS messages, 4 utility
WhatsApp reminders and 6 emails per month, including tenant/manager recipients
in those counts. This is an example workload, not measured behavior:

`2 x K0.24 + 4 x K0.08 + 6 x K0 = K0.80 per occupied unit/month`.

Use **K2 per occupied unit/month as an initial messaging budget allowance** for
pricing exploration, leaving room above that example for extra reminders,
segments and provider differences. It is not a quote, a guaranteed ceiling, or
an allowance for unlimited campaigns. Recalculate from actual deliveries once
providers and reminder schedules are chosen.

| Occupied units across all customers | Messaging allowance | Baseline + messaging | Average per occupied unit |
| --- | ---: | ---: | ---: |
| 20 | K40 | K800/month | K40.00 |
| 100 | K200 | K960/month | K9.60 |
| 500 | K1,000 | K1,760/month | K3.52 |

These totals exclude payment fees, domain renewal, storage/backups outside free
allowances, support labor, taxes and future infrastructure upgrades. They do not
establish how many units the $18 server can support. Fixed costs are shared across
Dwella's customers, not charged once for every landlord in this calculation.

## Payment costs: keep separate

Lenco's public Zambia page lists mobile-money collections at 1%, local cards at
3.5%, international cards at 3.8%, and payouts separately. Payouts up to K1,000
are K8.50-12 for mobile money (K8.50-10 for bank); K1,000.01-50,000 payouts are
K15-25. Actual account pricing and provider responses take precedence.

The chosen allocation is **tenant pays collection fee; landlord pays payout fee**.
Do not include those passed-through rent fees as a Dwella subscription expense
when they are fully recovered. They still require correct accounting and clear
disclosure at payment/withdrawal time.

Moving away from automatic payouts means the budget should count actual payout
events rather than assume one payout per tenant payment. For example, 10 tenants
each paying K3,000 creates K30,000 rent principal and approximately K300 collection
fees borne by tenants at the published 1% benchmark. If that landlord then takes
one combined payout, the published K15-25 payout band applies once, borne by the
landlord, rather than 10 times. Combined withdrawals are a cost-model example;
manual withdrawal and aggregation behavior are not asserted to be implemented.

Fee-on-top checkout arithmetic still needs definition: if Lenco charges 1% of the
entire amount collected, charging K3,030 does not leave exactly K3,000 after fees.
Use the account's actual fee basis and rounding to quote an amount that preserves
the rent principal. Likewise define whether payout fees are deducted from the
requested withdrawal or charged on top, and show the amount the landlord receives.

Subscription payments into Dwella's own Lenco account also incur the applicable
collection fee. Do not attach a landlord payout fee to subscription revenue
retained by Dwella. Recovery of subscription collection fees is a separate decision
from the agreed tenant-rent fee allocation.

## Other cost inputs

- R2 Standard: first 10 GB-month free per account, then $0.015/GB-month, plus
  operations beyond free request allowances; egress is free. At 100 GB average
  storage, 90 GB paid storage is $1.35, or K27/month at the assumed FX, before
  request charges. Free allowances are shared by buckets.
- Generated PDFs and signatures currently occupy PostgreSQL storage; they are
  not all in R2. Backups, retention and eventual server disk upgrades still cost.
- Domain renewal: actual annual invoice divided by 12; amount not yet supplied.
- Customer onboarding/support, manual reconciliation and disputes: human time;
  no defensible per-customer average yet. Chargebacks/refunds may add fees.
- Monitoring, recovery storage, upgrades and Handy overages: confirm what the
  current bills include before adding separate subscriptions or assuming zero.

For Claude's tier proposal, choose bounded message allowances and model support
time as well as unit counts. Keep passed-through payment fees explicit and separate
from subscription revenue. Revisit the budget after observing real monthly usage.

## Sources checked

- [Africa's Talking Zambia tariff within international SMS pricing](https://africastalking.ug/sms/bulksms)
- [Meta current pricing overview](https://whatsappbusiness.com/products/platform-pricing/)
- [Dated Meta USD rate card, effective July 2025, mirrored by Gupshup](https://www.gupshup.ai/resources/wp-content/uploads/2025/09/USD_July2025.pdf)
- [Lenco Zambia public pricing](https://lenco.co/zm/pricing)
- [Gmail sending limits](https://support.google.com/mail/answer/22839?hl=en)
- [Cloudflare R2 pricing](https://developers.cloudflare.com/r2/pricing/)
