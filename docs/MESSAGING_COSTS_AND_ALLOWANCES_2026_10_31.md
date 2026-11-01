# Optional messaging costs after mandatory operational email

2026-10-31. Cost model and recommendation, not activated prices or a message-credit ledger. Existing subscription/cost drafts were left untouched because they already contain separate edits.

Follow-up direction on 2026-10-31: the user requested separate customer-paid SMS/WhatsApp purchases. See `MESSAGING_TOP_UP_PLAN_2026_10_31.md`. Its recommended default is separate paid balances without a bundled allowance; the 30-included-message suggestion below remains historical/unapproved. Cost scenarios below still illustrate provider expenditure.

## Recommendation

Keep operational email and in-app access outside paid credits. Prefer WhatsApp for optional payment/repair summaries, with a secure Dwella link for invoices/receipts; use SMS selectively where WhatsApp is unsuitable. Do not charge incoming messages or treat every bot prompt as a paid outbound message. Both phone channels remain opt-in, so turning one on does not replace required email.

Replace the ambiguous six/eight mixed-credit proposal with **a proposed pool of 30 utility WhatsApp notifications per purchased capacity slot per month**, including tenant and manager recipients. Keep SMS as a separately priced prepaid allowance based on actual segments. This is a review recommendation; the implementation does not grant/debit credits or change plan prices.

This follows capacity billing and makes costs clearer than pretending that a WhatsApp utility message, marketing message and SMS segment have equal cost. Twenty notifications could be a lower starting point if beta usage is low; 30 provides room for maintenance and approval conversations. Measure actual billable outcomes before publishing the allowance/top-up price. Marketing campaigns are excluded from this recommended operational allowance.

## Inputs and confidence

| Input | Planning figure | Evidence/limitation |
| --- | ---: | --- |
| Zambia SMS, entry band | K0.24 per segment | Africa's Talking public Zambia table, checked 2026-10-31; larger spend bands list K0.21/K0.19/K0.17. Confirm tax, route, sender registration and account quote. |
| WhatsApp utility notification | K0.08 per billable delivery | Provisional existing worksheet benchmark of USD 0.004 × user-selected K20/USD modelling rate. Current account-specific Zambia rate was not retrieved; this is not a verified October tariff. |
| WhatsApp marketing | K0.45 per billable delivery | Provisional USD 0.0225 × K20 benchmark; excluded from recommended allowance. |
| Email | Existing email infrastructure/quotas | No customer credit deduction. Sender subscription/capacity is a platform cost, not infinite free delivery. |

The K20/USD figure is the user's modelling assumption, not a fresh market exchange-rate claim. Numeric WhatsApp benchmarks come from the existing worksheet's older rate card; Meta's current public overview confirms market/category/delivery-based pricing and free service/qualifying utility replies, but its linked current rate-card endpoint returned 429 during this check. Confirm the actual account tariff before launch, including any provider markup, tax or changed service-message terms. Do not budget the whole conversation as guaranteed free.

Sources: [Africa's Talking pricing](https://africastalking.ug/pricing?lang=en) (Zambia section; main africastalking.com pricing returned 403), [Zambia overview](https://zambia.africastalking.com/), [Meta pricing](https://whatsappbusiness.com/products/platform-pricing/), and existing `OPERATING_COSTS_2026_10_26.md` for the explicitly provisional WhatsApp figures.

## Per-unit monthly scenarios

These count all tenant/manager recipients in the workload. They assume utility category for chargeable WhatsApp messages, no volume discount and one SMS segment unless shown otherwise. They are provider-cost estimates before tax, sender/two-way-number setup, optional provider markup and support/operational costs.

| Workload per capacity slot/month | Per slot | 50 slots | 700 slots |
| --- | ---: | ---: | ---: |
| 8 utility WhatsApp notifications | K0.64 | K32 | K448 |
| 20 utility WhatsApp notifications | K1.60 | K80 | K1,120 |
| 30 utility WhatsApp notifications | K2.40 | K120 | K1,680 |
| 30 one-segment SMS | K7.20 | K360 | K5,040 |
| 30 two-segment SMS | K14.40 | K720 | K10,080 |
| 20 utility WhatsApp + 5 one-segment SMS | K2.80 | K140 | K1,960 |
| 40 utility WhatsApp + 10 one-segment SMS | K5.60 | K280 | K3,920 |

Formula: `utility WhatsApp deliveries × K0.08 + SMS segments × K0.24`.

At the proposed 30 WhatsApp allowance, 10 purchased slots pool 300 messages (K24 provisional cost), 20 pool 600 (K48), 50 pool 1,500 (K120), and 700 pool 21,000 (K1,680). These are pooled capacity-based allowances, not 30 messages reserved individually for each occupied tenant.

For comparison, 100 one-segment SMS cost approximately K24 before extras; 100 provisional utility WhatsApp deliveries cost K8. A shared K40/100-credit retail price from the old draft therefore has very different margins across the two channels. Do not copy that price into a new mixed wallet without deciding its cost weights and inclusions.

## Why eight can run out

A month containing an invoice, all five due/overdue reminders, one confirmed payment, one repair through reported/scheduled/started/completed and one public repair comment could create:

- Invoice issued: tenant + one manager = 2 notifications.
- Five rent reminder dates: tenant = 5.
- Payment received: tenant + one manager = 2.
- Four repair stages: tenant + one manager = 8.
- One public repair comment: tenant + one manager = 2.

That is **19 notifications**, before lease-expiry notices, corrections, payment problems, withdrawals, extra managers or manually composed notices. This is an illustrative busy-month scenario, not measured current usage. Required email covers these even when every optional phone channel is off.

Optional channels can both be enabled; this is additional delivery, so the same event sent by SMS and WhatsApp incurs both channel costs. Prefer enabling WhatsApp alone for routine operational messages rather than assuming automatic cross-channel fallback. Payment-proof chat remains a separate proposed feature and would add its own workload when implemented.

## SMS segmentation and remaining decisions

SMS charges are per encoded segment: typical GSM-7 is 160 units for one segment and 153 per segment when concatenated; Unicode commonly reduces these to 70/67. Extension characters can count twice and emoji may use surrogate pairs. A long receipt reference + URL + opt-out footer may be multiple segments even when the human sees one text bubble. Use provider-reported encoding/segment count for settlement, not JavaScript string length. Keep templates concise and measure real payloads before setting allowances.

Suggested commercial rules to approve later:

1. Thirty pooled utility WhatsApp notifications per purchased capacity slot; monthly reset even for annual subscriptions. No charge for incoming or Meta-free replies unless an explicitly priced provider service applies.
2. Separate SMS top-ups, with estimated segment cost shown before campaigns; no mandatory SMS fan-out.
3. Reserve paid allowance before dispatch, settle to known billable provider outcomes, reconcile uncertain sends without double deduction, and never charge a technical duplicate twice.
4. At exhaustion, hold optional paid sends and show the manager the reason. Required email, existing payment confirmation, records and tenant access continue.
5. Final provider/account tariff, tax, FX buffer, setup fees, top-up prices/expiry and rollover are unresolved. No subscription charging or new allowances have been enabled by this work.
