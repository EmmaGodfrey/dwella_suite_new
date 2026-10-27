# Dwella subscription plan — proposal

Drafted 2026-10-26 by Claude for the user and Codex to review. **Nothing is implemented.** Decisions the user has made are listed under "What is already decided"; everything else is still a proposal. It builds on:

- [OPERATING_COSTS_2026_10_26.md](OPERATING_COSTS_2026_10_26.md) for cost inputs;
- [SUBSCRIPTION_READINESS.md](SUBSCRIPTION_READINESS.md) for the access foundation that already exists;
- [LENCO_PAYMENTS_SETUP.md](LENCO_PAYMENTS_SETUP.md) for payments.

## What is already decided

- Three paid tiers, plus a fourth tier priced per unit above a threshold.
- No freemium.
- Be upfront with property managers about what Dwella costs.
- Tenants pay the collection fee; landlords pay the payout fee.
- The product is moving away from automatic payouts.
- Subscription money is collected into Dwella's own Lenco account, separate from rent. It never goes through a landlord payout.
- Tenants never pay a subscription.
- **2026-10-26:** Starter stays small, up to 5 units, possibly fewer. It's deliberately small so most landlords pick Standard.
- **2026-10-26:** Portfolio uses per-unit rates that get cheaper with size (graduated bands, below).

## Principles

1. **One price, three kinds of cost, all shown.**
   - The subscription pays for Dwella.
   - Payment fees are passed on at cost.
   - Messaging is included up to an allowance.

   Nothing is marked up silently.
2. **Never hold anyone's money or records hostage.** A lapsed subscription never stops these:
   - a tenant paying an invoice that already exists;
   - a landlord withdrawing money that has been collected;
   - anyone viewing or exporting history.
3. **Tiers grow with portfolio size, not with access to the basics.** Every tier includes rent collection, invoices, receipts, the tenant portal, leases and maintenance. They are the reason to use Dwella, and they're how rent flows through it.
4. **No price jump at a tier boundary.** Moving up one unit should never cost much more than the unit itself.

## Billable unit

**A unit with an active lease on the billing date.**

- Vacant units are free and unlimited. Charging for empty units feels unfair, and vacancies are common.
- It's hard to cheat, because invoicing a tenant requires a lease.
- **Gap in the code:** the existing `capacity_guard` counts *stored records, including archived ones*. That is a technical limit, so it can't serve as the billing meter. Billing needs its own count of units with an active lease, saved on each billing date.

## Proposed tiers

All prices in kwacha. The rate stays fixed in ZMW, so it doesn't move with the dollar.

| | **Starter** | **Standard** | **Professional** | **Portfolio** |
|---|---|---|---|---|
| Leased units | up to 5 | up to 20 | up to 50 | 51 or more |
| Monthly | **K150** | **K400** | **K850** | **K850 + graduated per-unit rates (below)** |
| Annual (2 months free) | K1,500 | K4,000 | K8,500 | 10 × monthly |
| Cost per unit at the cap | K30 | K20 | K17 | about K16 at 100 units, about K11 at 700 |
| Share of rent roll (K3,000 average rent, at cap) | 1.0% | 0.67% | 0.57% | about 0.5% |
| Team members (managers) | 1 | 2 | 5 | Unlimited |
| Bulk unit and tenant import | — | ✓ | ✓ | ✓ |
| Handy assistant | — | ✓ (fair use) | ✓ (fair use) | ✓ (fair use) |
| Message credits (SMS/WhatsApp) per leased unit per month | 6 | 6 | 8 | 8 |
| Support | Email | Email | Priority (WhatsApp) | Priority plus onboarding help |

**Portfolio rates.** These are graduated, like tax brackets: each rate applies only to the units inside its band, so the price never jumps.

| Leased units | Rate per unit per month |
|---|---:|
| 1–50 | included in the K850 base |
| 51–200 | K15 |
| 201–500 | K10 |
| 501 and above | K7 |

Examples:
- **100 units:** K850 + 50 × K15 = **K1,600**.
- **300 units:** K850 + 150 × K15 + 100 × K10 = **K4,100**.
- **700 units:** K850 + 150 × K15 + 300 × K10 + 200 × K7 = **K7,500**. That's about K10.70 per unit, close to Nyumba Zetu's rate for large portfolios. Customers this size are offered an annual contract and may negotiate.

**What every tier includes:**
- properties, units and tenants;
- invoices, partial payments and receipts;
- online rent collection by mobile money and card;
- withdrawals;
- the tenant portal;
- lease documents and electronic signing;
- maintenance;
- the dashboard;
- unlimited email and in-app notifications.

**Why these numbers:**
- Property agents in Zambia typically charge around 10% of rent to manage a property. Dwella works out to 0.5–1% of the rent roll, so it's clearly worth paying for.
- Starter is cheap enough for someone with one or two units. At K150 a month it is about 5% of one K3,000 rent. Raise or lower it once you've talked to small landlords.
- **There's no jump at the threshold.** 50 leased units costs K850 and 51 costs K865. The per-unit rate continues the falling curve.
- **There is a jump between Starter, Standard and Professional.** For example, 6 units costs K400 against K150 for 5. **This is intentional** (see "Pricing psychology"). Customers who go over keep their tier for one billing cycle (see "Going over a tier limit").

**Pricing psychology:**
- **Starter is an entry point, not the main plan.** Its small limit and higher cost per unit (K30, or K50 if capped at 3 units) make Standard look like the obvious choice, at K20 per unit with four times the units.
- **Mark Standard "Most popular"** and give it the visual emphasis on the pricing page.
- **Show the cost per unit on every tier,** so the saving from moving up is visible.
- **Show Portfolio as well,** even though few customers choose it. A large figure on the page makes the middle tiers look reasonable.
- **Show annual prices as "2 months free"** rather than as a percentage.
- Remove the jump only if small landlords drop out at the trial-to-paid step.

**Message credits:**
- One SMS segment or one WhatsApp message counts as one credit.
- Credits are pooled across the workspace and reset every month.
- At the costs in the worksheet, 8 credits costs Dwella at most about K1.92 per unit. That's within the K2 messaging budget Codex proposed.
- Top-up bundle: 100 credits for K40. That's roughly 1.7× the SMS cost, and it covers providers changing their prices.
- Email and in-app notifications never use credits.

## Market comparison (checked 2026-10-26)

These are vendor-published prices, converted at USD 1 = K20 (the rate the user confirmed on 2026-10-26) and KES 129, so **KES 1 ≈ K0.155**. Recheck the rate before publishing prices. I found no published kwacha prices from Zambian vendors; Evolution and Broll quote on request.

Monthly price by portfolio size (leased units):

| Platform | 5 units | 20 units | 50 units | 100 units | Notes |
|---|---:|---:|---:|---:|---|
| **Dwella (proposal)** | **K150** | **K400** | **K850** | **K1,600** | Payment fees passed on, none kept |
| RentSawa (KE) | K155 | K390 | K390 | from K1,160 | Starter covers 15 units, Pro 50; SMS allowance; staff accounts from Pro; 7-day trial |
| HomeSpot (KE) | K390 | K390 | quote | quote | Starter covers 20 units |
| Nyumba Zetu (KE) | about K140 + minimum | about K560 | up to K1,400 | falls towards K9/unit | KES 180/unit, falling to KES 60/unit at scale; 20% off annual; minimum not published |
| My Rent Kenya (KE) | K78 or 1% of rent | K310 or 1% | K775 or 1% | K1,550 or 1% | KES 100/unit with your own paybill, or 1% of collected rent and no subscription |
| TenantCloud (US) | K300–500 | K580–700 | K1,000–1,200 | from K2,000 | Priced by number of leases (10/30/60) |
| Buildium (US) | from K1,240 | — | — | — | Higher tiers K3,840 and K8,000 |
| AppFolio (US) | — | — | K5,960 minimum | K5,960 | $1.49/unit with a $298 minimum |

What it shows:

- **Small portfolios (up to 20 units):** Dwella sits in the middle of the Kenyan products. US products cost 2–8 times more.
- **Around 50 units:** RentSawa's flat price is about half of Dwella's. Nyumba Zetu and TenantCloud cost more than Dwella.
- **Starter's 5-unit cap is tight.** RentSawa covers 15 units for about the same money. **Suggested change:** Starter up to 10 units at K150–200. This also softens the jump to Standard.
- **The tier structure looks right.** The closest competitor (RentSawa) also uses a flat price per unit band, an SMS allowance that grows with the tier, and staff accounts on higher tiers.
- **Kenyan products mostly keep nothing from rent payments.** My Rent Kenya is the exception: it offers 1% of collected rent instead of a subscription. Dwella's "fees at cost" approach is a clear selling point.
- **Prices should probably sit at or below Kenya's.** Incomes and rents in Zambia are generally lower than in Kenya, so treat Kenyan prices as a ceiling.

Sources:
- [RentSawa](https://rentsawa.com/)
- [Nyumba Zetu](https://www.nyumbazetu.com/)
- [My Rent Kenya pricing](https://myrentkenya.com/pricing)
- [HomeSpot](https://www.homespot.ke/property-management-software-kenya)
- [TenantCloud pricing](https://www.tenantcloud.com/pricing)
- [Buildium pricing](https://www.buildium.com/pricing/)
- [AppFolio figure via CostBench](https://costbench.com/software/property-management/buildium/alternatives/)
- [Zambian vendors (M&J Consultants)](https://mjconsultants.co.zm/insights/property-management-software-in-zambia-a-complete-guide-for-real-estate-agents-and-landlords/)

Kenyan figures are vendor claims from their websites and should be rechecked before anything is published.

## What it costs Dwella (check against the worksheet)

- **Fixed costs:** the server costs $18 now. Handy costs about $20 if it goes ahead. That's about **K760 a month** at today's K20/USD.
- **Messaging:** about K2 per leased unit per month at most.
- **Collecting the subscription:** Lenco charges 1% on mobile money. Dwella absorbs it. It's about K1.50 on a Starter invoice.
- **Breakeven on fixed costs:** about 6 Starter customers, 2 Standard, or 1 Professional.

Illustrative mix, not a forecast:

| Customers | Revenue / month | Messaging | Collection fees | Fixed costs | Left for support and growth |
|---|---:|---:|---:|---:|---:|
| 10 Starter (avg 4 units), 5 Standard (avg 15), 2 Professional (avg 40) | K5,200 | about K390 | about K52 | about K760 | **about K4,000** |

Not yet included: support time, domain, backups, taxes, future server upgrades. Revisit after three months of real usage.

## Payment fees: how they are shown

**Rent collection (paid by the tenant):**
- Checkout shows the rent, the fee and the total before the tenant confirms.
- At Lenco's published rates the fee is 1% for mobile money and 3.5% for local cards.
- **Still to define (as Codex noted):** Lenco charges 1% of the *whole* amount collected. Adding exactly 1% on top therefore leaves the landlord slightly short of the rent. The total has to be grossed up, roughly rent ÷ 0.99, with a stated rounding rule. Confirm with Lenco how the fee is calculated on our account.

**Withdrawals (paid by the landlord):**
- Before confirming, the landlord sees: amount, payout fee (K8.50–25 depending on the amount), and amount received.
- The withdrawal screen notes that one combined withdrawal costs a single fee.

**Billing settings get a "What Dwella costs" section** with three short blocks:
- your plan;
- payment fees (at cost, Dwella keeps nothing);
- messaging (credits used this month, how many remain, top-ups).

**Dwella takes no margin on payment fees.** If that changes later, it has to be shown as a separately named platform fee.

## Trial, sign-up and beta

- **No free tier.** New workspaces get a **30-day trial with every Professional feature** and 50 message credits in total. No payment is taken at sign-up.
- When the trial ends, the plan is picked automatically from the number of leased units, and the manager confirms it and pays.
- **Beta workspaces:**
  - every feature stays open until a published switch-on date, announced at least 30 days ahead;
  - after that, a **founding price at 50% off for 12 months**. Alternative: keep their tier price locked for 12 months.

## Billing cycle and collecting subscription payments

- Billing is monthly or annual, starting from the day the subscription begins.
- **Mobile money can't be charged automatically.** Every charge needs the payer to approve it on their phone. So:
  - send a reminder 7 days and again 1 day before the due date, by email and in-app;
  - the Billing page shows "Pay K400 now", using the same native mobile-money form as rent, or Lenco's hosted card checkout;
  - recommend annual plans, which means one approval a year;
  - payments go to Dwella's Lenco account with **no payout step**.
- Each payment produces a subscription invoice and receipt in Dwella's style. Whether ZRA-compliant invoices are needed is a later decision.

## Going over a tier limit

- **Adding a lease is never blocked**, because blocking it would block rent collection.
- On the next billing date, the plan follows the count of leased units:
  - moving up takes effect then, with a notice in-app and by email;
  - moving down happens automatically on the next billing date.
- **Optional soft rule:** a customer can stay one billing cycle above their tier limit before the upgrade applies.
- **Team member limits are firm,** because adding a member is a deliberate action. At the limit, the UI offers an upgrade.

## When a payment is missed

| Days after the due date | State | What happens |
|---|---|---|
| 0–7 | **Grace period** | Everything works; a banner and reminders ask for payment |
| 8–30 | **Restricted** | No new invoices, leases or signing invitations, and no manager messages. Still allowed: viewing, exporting, tenants paying invoices that already exist, landlords withdrawing collected money, and maintenance updates |
| 31 days or more | **Paused** | As Restricted, and scheduled reminders stop. Data is kept. |

- Paying at any time returns the workspace to Active straight away.
- Data is only deleted if the customer asks or if a written retention policy says so. Neither exists yet.
- These rules fit the existing foundation: removing a feature never deletes records, and signing invitations already sent stay valid.

## How it fits the existing code

The foundation (`subscriptions.WorkspaceAccessPolicy`, `require_feature`, `capacity_guard` and the entitlements API) stays the single place access is enforced. A billing layer sits on top of it and translates plan state into policy:

- `Plan` catalogue: tier, monthly and annual price, member limit, credits per unit, feature grants.
- `WorkspaceSubscription`: plan, interval, status (trial, active, grace, restricted, paused, cancelled), period start and end.
- `SubscriptionInvoice` / `SubscriptionPayment`: linked to a Lenco collection with **no payout**.
- **Billable-unit meter:** the count of units with an active lease, saved on each billing date.
- **Message credit ledger:** monthly grant, deductions per send, top-ups. A message that would overspend is held, which matches the Messaging design.
- **New capacity resource:** `members`. Only `properties`, `units` and `tenants` exist today.
- Restricted state is mapped to `feature_overrides` for: invoice creation, `lease_documents`, `lease_signing`, and manager `email_messages`, `sms_messages` and `whatsapp_messages`.
  - Rent checkout for invoices that already exist, plus withdrawals, must **stay** allowed.
  - `online_payments` currently guards *starting* a checkout. Restricted state must not switch it off for invoices that already exist.

**Suggested order:**
1. Design in Figma (pricing page, Billing "What Dwella costs" section, plan-change and payment-due states).
2. Plan catalogue and subscription model, still with beta defaults.
3. Unit meter and credit ledger.
4. Subscription collection through Lenco.
5. Grace and restricted states.
6. Switch-on date.

Each step is its own small commit.

## Decisions needed from the user

1. Starter limit: 5 units (current) or 3. Starter, Standard and Professional prices and the Portfolio band rates are agreed in principle; they're final once the beta customers have seen them.
2. Billable unit: units with an active lease, as recommended, or every unit.
3. Whether Handy is left out of Starter, which depends on its final price and usage cap.
4. Credits per unit and the top-up price.
5. Trial length, and the beta founding discount or price lock.
6. Annual discount: two months free, or something else.
7. Whether prices include VAT or turnover tax; check Dwella's tax registration.
8. The grace and restricted timings above.
9. Tier names: Starter / Standard / Professional / Portfolio are placeholders.

No subscription prices, charges, provider settings or entitlement changes have been made.
