# Separate SMS and WhatsApp purchases

Date: 2026-10-31

Status: proposal requested by the user. No wallet, top-up checkout, customer charges, provider activation or application implementation is authorised by this draft.

## 1. Recommended product

Landlords/property managers purchase optional messaging for their workspace. Tenants do not need to buy credits to receive rent or repair notices. Any authorised manager can use the shared workspace allowance; purchases and spending are audited to the initiating user.

| Channel | What the customer buys | What is deducted |
| --- | --- | --- |
| Email and in-app | Included operational communication | No messaging credits; email remains mandatory |
| SMS | Packs of outbound SMS segments | Actual chargeable segments, under an approved quote |
| WhatsApp | A dedicated kwacha messaging balance | The published channel rate for a chargeable notification; qualifying free replies deduct zero |

Show **SMS credits** and **WhatsApp balance** separately under Settings → Messaging. Keep one underlying ledger/reservation implementation with explicit account units, but never mix a count of SMS segments with a kwacha balance or automatically exchange between them.

Recommended initial scope: Zambia domestic SMS, approved WhatsApp utility notifications, manual top-ups and no automatic recharge. Keep marketing campaigns, international SMS, customer-owned provider accounts and arbitrary conversational bot billing out of the first release.

This becomes the recommended default in place of the earlier unapproved six/eight mixed-credit proposal and the later suggested 30 included WhatsApp messages per capacity slot. Messaging is a separate optional purchase; subscription capacity prices remain unchanged. Any future included allowance or beta gift must be an explicitly labelled promotional grant, separate from purchased balances.

## 2. Customer experience

**Buy SMS:** select 100 / 500 / 1,000 credits, see the total and fees, pay through Dwella, then see the credited pack and receipt. Explain beside the quantity: **One credit is one SMS segment. A long message can use multiple credits.** Do not label a pack “100 texts” without that qualification.

**Top up WhatsApp:** select K20 / K50 / K100 or a bounded custom amount. These are example denominations, not final minimums. Explain that message counts vary by the approved template, recipient market and billable category; display a useful estimate without promising a universal number of messages.

Before a composed send, show recipient count, SMS segments or WhatsApp estimated maximum spend, and remaining balance after reservation. Confirm once. If recipients/content/category change, rebuild the quote. Automatic optional notifications use a workspace-approved tariff and spending limit, so the landlord need not confirm every rent notice; an opt-in to the channel must explicitly explain these automatic deductions.

At a low balance, show an in-app banner and send one required operational email per threshold crossing. At zero/insufficient balance, email and in-app updates continue, while the optional phone notification is held with a clear reason. Buying credits never silently enables a channel, consents on behalf of tenants, or sends a backlog of old notices.

Only paid sends need a positive balance: incoming messages and genuinely zero-priced replies remain usable. A tenant can still submit a claim/request through any otherwise enabled channel when the landlord's paid balance is empty; its paid alert can fall back to required email/in-app. Resuming held paid messages requires explicit review of still-relevant notices and a fresh quote; do not revive stale reminders merely because a top-up arrived.

Purchased units carry over; they do not reset monthly or expire by default in this proposal. Promotional units, if later offered, have separately disclosed expiry and are spent first. Do not erase purchased value at a subscription renewal or downgrade.

## 3. Illustrative prices and economics

No selling price is approved. Use the following to discuss the model, not publish a tariff:

| Example SMS pack | Example retail price | Planning provider cost at K0.24/segment | Gross difference before other costs |
| --- | ---: | ---: | ---: |
| 100 segments | K40 | K24 | K16 |
| 500 segments | K200 | K120 | K80 |
| 1,000 segments | K400 | K240 | K160 |

The examples use K0.40 retail per segment with no assumed volume discount. Gross difference is not net profit: taxes, provider setup/route fees, collection fees, failed-but-billable sends, rate movements and support still need covering. If all recipients require two segments, 100 credits cover 50 such recipient deliveries.

For WhatsApp, a **purely illustrative** K0.12 retail utility rate against the existing provisional K0.08 provider benchmark would give about 416 paid utility deliveries from K50 (K49.92 spent; K0.08 left). Actual approved tariffs must be obtained first. Do not promise K0.12 as a live price or imply that every chat bubble is a paid utility message.

Set WhatsApp retail rates by supported recipient market/category and publish a versioned tariff. Start with Zambia utility templates and exclude marketing rather than subsidising differently priced messages under one credit. Respect provider-free service/qualifying utility replies: recommended customer charge is zero when the direct provider charges zero. Any future separately charged automation/provider service must be explicit, not disguised as a Meta fee.

Top-up checkout shows separately:

- Pack/balance value purchased.
- Applicable taxes and whether displayed prices include them.
- Collection/checkout fee, if passed through.
- Total payable and the exact credits/balance to be added.

Choose and disclose one fee policy before implementation. Recommendation: preserve the displayed messaging value and show any passed-through checkout fee explicitly; do not tell a customer they bought K50 and silently credit K48. Alternatively include the processing cost in the published pack price. Minimum top-ups should follow the real provider's fixed/percentage collection cost, not a guessed minimum. No current collection-fee rate is assumed here.

## 4. Fit with current Dwella

The existing operational notification work provides event intents, sender controls and delivery history. It does **not** yet provide commercial wallets, usage settlement or top-ups. The separate paid-channel gate belongs immediately before the provider-send claim, and must cover **both** `OperationalDelivery` and legacy/composed `MessageDelivery`; otherwise optional campaigns could bypass the balance.

Use the current Django/PostgreSQL application, existing scheduler/worker and provider adapters. No new broker, service or chatbot platform is needed. Keep API calls in frontend Services with query/mutation hooks. Existing settings need only balances, a purchase drawer, recent usage/top-ups and low-balance controls; existing message previews gain a cost row and insufficient-balance state. Detailed UI design/review comes before implementation.

Lenco is the existing intended Dwella collection provider, but the current rent `Collection` is coupled to a tenant invoice and landlord destination. **Do not reuse that rent collection/ledger by inventing a tenant, rent invoice or payout destination.** A messaging purchase is revenue/prepaid service value paid to Dwella, with no landlord payout or rent balance effect. Implement its separate commercial checkout through an appropriate shared provider transport after verifying account/API support. Payment integration implementation remains Claude-owned; this explicitly requested draft does not implement it.

Managers should not need an Africa's Talking or Meta account. Dwella operates the providers and sells the optional messaging service. Customer-owned providers may be a separate later enterprise option; provider credentials never appear in landlord settings.

## 5. Purchase and crediting flow

1. Authorise the current workspace manager, active workspace and purchase eligibility. Verify the channel is genuinely available before selling a pack the workspace cannot use. Freeze the SKU, units, price, tax/fee treatment, currency and expiry of the checkout quote.
2. Create one `MessagingTopUp` with a workspace-scoped idempotency key and short-lived quote. Start a dedicated provider checkout; the public return page only reports pending status.
3. Validate the signed callback and reconcile the provider transaction server-side: merchant/account, reference, currency, amount, environment and successful collection state must all match. Polling and callbacks converge on the same operation. A screenshot or browser success parameter never credits a balance.
4. In one short transaction, lock the top-up/account in a consistent order, insert a unique purchase ledger entry, update the account summary, mark credited and queue the purchase receipt email. Repeated callbacks return the same result and cannot add more credits.
5. Failed/abandoned checkout adds nothing. An uncertain provider result remains pending/review; never blindly initiate a second charge. A late verified success for an expired checkout is reviewed/reconciled without losing money or silently granting the wrong SKU. If a channel/workspace becomes unavailable after payment, retain the customer's purchased value and offer a reviewed resolution/refund.

Keep amounts as Decimal/integer minor units, never floating point. Display customer currency explicitly. A failed receipt email does not undo a valid top-up, and a successfully emailed receipt does not itself establish that payment settled.

## 6. Usage reservations, failures and retries

Account summary distinguishes **available**, **reserved** and **spent**. The customer's SMS quantity and WhatsApp money remain separate. Ledger entries preserve purchase, promotional grant, spend, release, refund and adjustment history; no overwriting balances or deleting financial evidence.

| Stage/outcome | Accounting rule |
| --- | --- |
| Preview | Calculate an estimate; no deduction |
| Confirmed send / automatic optional event | Freeze recipient, content/template, tariff and maximum spend; reserve atomically |
| Insufficient balance | No phone-provider call; show/hold the optional message; required email is unaffected |
| Known non-billable rejection before acceptance | Release the reservation once |
| Known provider-billable outcome | Settle against the frozen customer tariff and provider evidence, once |
| Timeout, crash after submission or ambiguous callback | Keep the reservation marked uncertain; reconcile or route to review; do not resend or refund blindly |
| Definitive failure after provider acceptance | Apply the provider contract's billing rule; some failed deliveries can still be billable, so failure is not automatically a refund |
| Provider-free WhatsApp reply | Record zero-priced usage; do not deduct paid balance |
| Technical retry / duplicate callback | Same reservation and settlement key; no second deduction |

**Billing evidence is a release prerequisite.** The current operational history records acceptance/review and is not a complete provider billing ledger. Add correlation IDs, delivery/pricing evidence and reconciliation for both queues before charging per billable outcome. In particular, do not use absence of a callback, a read receipt or a generic `sent` status as proof of a charge or non-charge. Confirm the SMS provider's actual charge point and Meta's current category/window rules for the configured account.

For SMS, account for real GSM-7 extension characters, Unicode/surrogate pairs and concatenation. Verify the provider sends the quoted encoding without silently changing text/transliteration; reconcile actual segment counts. For WhatsApp, the tenant and landlord have separate recipient windows and can have separate charges.

Customer-authorised maximum spend is a hard cap. If upstream billing exceeds it through reclassification/segmentation discrepancies, hold the disputed adjustment for review and let Dwella bear an unapproved excess; do not overdraw the customer or silently raise the price after sending. Fix templates/quotes and future tariffs rather than retroactively charging an undisclosed marketing rate.

Monitor uncertain reservations and escalate unresolved ones to support after a proposed 24 hours. Some providers may never supply conclusive evidence; require an audited policy-based resolution rather than leaving an unexplained hold forever. Any goodwill credit is funded and labelled by Dwella, and later reconciliation cannot debit the customer twice.

## 7. Proposed records and invariants

| Record | Purpose |
| --- | --- |
| `MessagingAccount` | Workspace + channel/unit, materialised available/reserved summaries, version; one account per workspace/channel |
| `MessagingProductVersion` | Immutable pack/retail tariff, supported market/category, units/currency, tax/fee treatment and validity |
| `MessagingTopUp` | Buyer/workspace, frozen quote, provider reference, verified payment/credit/refund states and receipt link |
| `MessagingLedgerEntry` | Immutable signed movement with account, unit, event/reference, actor and unique operation key |
| `MessagingReservation` | Unique canonical delivery identity covering either queue, tariff snapshot, reserved/settled/released units, uncertain state |
| `MessagingProviderEvidence` | Private, bounded/redacted provider pricing and outcome evidence, tied to a delivery/top-up |

Do not attach reservations to an arbitrary generic model path supplied by a client. Use explicit allowlisted delivery relations and an XOR constraint where separate foreign keys are needed. A reservation must resolve to exactly one workspace and channel.

Use PostgreSQL account-row locks plus non-negative summary checks to prevent two simultaneous campaigns spending the same credit. Lock multiple accounts in stable order; no network calls while holding the financial locks. An account-summary update, ledger entry and domain state transition commit together. Use unique constraints for each provider top-up credit, delivery reservation and final settlement.

Ordinary balance reads use the materialised summaries; they must not sum growing histories on every send/page. Reconcile summaries with the immutable ledger using a bounded durable cursor, and investigate discrepancies. Keep ledger/evidence retention distinct from transient callback/worker logs. Private account/ledger/top-up tables receive the repository's RLS/direct-assistant restrictions; tenant APIs cannot view or spend a landlord's balance.

## 8. Balances, refunds and subscription changes

- No withdrawal, cash transfer to another workspace or conversion into landlord rent funds. This is prepaid messaging usage, not a general cash wallet.
- No automatic top-up initially. Later auto-recharge needs separate explicit consent, a per-recharge/monthly cap and a safe supported payment mandate; do not assume the rent checkout provides one.
- Purchased SMS credits remain fixed segment units under the disclosed scope. A provider increase affects future pack prices; do not silently shrink existing packs. For a permanently withdrawn route/service, offer an appropriate reviewed unused-value resolution.
- WhatsApp monetary balances retain their kwacha value. Future sends use a displayed/versioned current tariff, with rate-change notice and standing-spend controls; existing reservations retain their agreed tariff.
- Recommended subscription downgrade/cancellation: preserve purchase/usage history and unused balances, provide refund/support access, and never block required email/rent payments. If an optional feature is unavailable, explain that before accepting another top-up. Do not forfeit purchased value merely because a plan changed.
- Refund policy, tax treatment and terms require review before sale. Refund only eligible unused, unreserved paid value to the original payment route, subject to the approved policy; grants are not refundable cash. Chargebacks freeze affected remaining value for review without changing rent balances. Never create a negative spendable balance to hide a disputed used purchase.

## 9. Minimal delivery phases

1. **Agree product rules:** separate paid messaging; SMS segment packs and WhatsApp kwacha balance; final retail rates, tax/checkout fees, carryover/refunds and spending caps. Earlier included-credit figures are not promises.
2. **Design existing-screen additions:** balances/purchase drawer, quote and fee breakdown, usage/history, low-balance notice, insufficient-balance send preview and admin reconciliation. No broad Settings redesign.
3. **Ledger/reservation foundation:** migrations, private access restrictions and both-queue adapters, feature off; synthetic credit grants for tests only. Cover concurrent overspend, rollback, isolation and idempotency before provider checkout.
4. **Verified top-up checkout:** dedicated commercial provider collection, immutable payment evidence and receipt email. Duplicate/replayed/forged callbacks, wrong merchant/currency/amount and uncertain collection tests; no live test charges without authorisation.
5. **Metered dispatch:** quoted encoding, channel-specific tariffs, provider billing evidence, safe reconciliation and bounded worker retries. Prevent the legacy/composed queue or future WhatsApp bot from bypassing the meter.
6. **Controlled pilot:** synthetic/allowlisted sends, then an explicitly authorised workspace pilot with modest limits. Reconcile balances and provider statements, review support costs, and only then publish prices/allowances.

Implementation follows plan → implement → validate, with small tagged commits, full shared-backend checks and a frontend build/flow check. In-place model switching is not exposed in this drafting runtime. This task ends at a reviewable plan; it does not activate balances, sell packs or alter notification behaviour.

## 10. Evidence and open decisions

Checked 2026-10-31: [Africa's Talking pricing](https://africastalking.ug/pricing?lang=en) has a Zambia SMS entry band of K0.24/segment with lower spend bands. [Meta pricing](https://whatsappbusiness.com/products/platform-pricing/) describes delivered-message, market/category-dependent charging and free service/qualifying utility replies. Exact account tariffs, categories, billing evidence, setup/two-way route costs and collection fees still need verification. Existing numeric WhatsApp benchmark remains provisional, as recorded in `MESSAGING_COSTS_AND_ALLOWANCES_2026_10_31.md`.

Default recommendation for review: **no bundled paid-channel allowance; SMS packs + a separate WhatsApp balance; manual top-ups; purchased value carries over; email continues regardless of either balance.** Final prices, minimums, fee bearer, tax/refunds, spend controls and any promotional allowance remain to be approved.
