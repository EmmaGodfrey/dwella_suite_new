# Manual landlord withdrawals — discussion draft

Prepared 2026-10-26 after the user requested pushing the reviewed MVP additions
and moving to the next item. This is a proposal, not implemented payment behavior.

## Established direction

- Keep Lenco. User reports collection fees are already charged to tenants through
  Lenco configuration. Do not add another application collection surcharge.
- Landlords pay payout fees. Move away from automatic per-collection payouts.
- Rent and Dwella subscription revenue remain separate accounting purposes.
- Start with the existing mobile-money destination. Bank destinations are an
  additional design/integration step, not silently included in this first slice.

## Proposed landlord flow

1. Billing shows available settled funds, funds awaiting settlement, withdrawals
   in progress and withdrawal history. Only the landlord's own workspace balance
   is available; the pooled Lenco balance is not their balance.
2. Open a Withdraw drawer, choose the amount and review receiving details.
3. Show amount received, Lenco fee, total deducted and balance remaining, then
   require explicit confirmation of that exact preview.
4. Reserve the total once and submit one transfer with one stable reference.
   Show pending until provider verification proves success/failure.
5. A timeout or uncertain outcome stays reserved and enters reconciliation.
   It must never produce a blind duplicate transfer or a second withdrawal.

User confirmed on 2026-10-26: enter **amount the landlord receives**. Show the
fee separately and reserve **amount received + fee** from the landlord balance.
Withdraw maximum must account for fee bands and rounding rather than subtracting
an arbitrary fee from the whole balance. Preserve exact two-decimal arithmetic.

## Existing code constraints

- `Payout.collection` is currently one-to-one. Successful settled collections
  create queued payouts in `_record_success`; the worker submits those records.
  This cannot represent one withdrawal funded by several tenant collections.
- Existing balance coverage/reservations and evidence rely on that collection
  link. Update them together; changing just the button or payout switch is not
  enough to make combined withdrawals correct.
- Existing transfers pay out the settled principal; known payout fees are treated
  as platform-account expenditure. New manual withdrawals must reserve both net
  payout and the landlord's fee without retroactively charging historical fees.
- Reuse provider status verification, immutable destination snapshots, encrypted
  exchange evidence, stable references and submission claims. Preserve all old
  collection/payment/receipt/provider references and in-flight transfers.

## Proposed implementation slices

1. Model withdrawal intent/preview, amount received, fee quote, total reservation,
   immutable destination and per-collection allocations. Keep legacy payouts
   identifiable and readable; prepare a migration/backfill with explicit invariants.
2. Calculate each workspace's available settled balance in the database, excluding
   settled amounts already paid/reserved. Include queued confirmed manual requests
   in reservations immediately. Never allocate pending collections or another
   workspace's funds. Acquire short locks in a consistent order.
3. Add bounded preview/confirm/history APIs with fresh workspace/manager/destination
   checks, expiry, input validation, throttling and idempotency. Preview must not
   submit a provider transfer. Cancellation only releases an unsubmitted intent.
4. Replace new automatic payout creation with available funds. Reconcile submitted
   legacy transfers normally. Before switching, explicitly handle every queued,
   submitting, pending, successful, failed and review record; no blanket retry or
   cancellation of uncertain money movements.
5. Extend the worker, fee reservations, reconciliation and admin evidence/history
   for manual withdrawals. Keep external calls outside locked transactions.
6. Refine existing Figma withdrawal/held-balance references, then implement the
   drawer, fee review, balance display and status/history against those APIs.
7. Test competing withdrawals, duplicate confirmation, insufficient funds including
   fees, partial settlements, permission removal, changed destinations, timeout,
   provider mismatches and migration compatibility on PostgreSQL. Deploy to test
   for the user's controlled verification before enabling a new live money flow.

## Fee information still to verify

The official transfer endpoint returns a `fee` in its response. A reliable
pre-transfer fee quote method has not been verified. Public Zambia pricing gives
ranges, so it is not an exact fee quote for a particular amount/operator/account.
Obtain authoritative account-specific fee rules or a supported quote capability
before enabling fee-bearing withdrawals. A mismatch must be visible and reconciled;
do not silently debit extra fees or use another landlord's reserved principal.

Sources checked 2026-10-26:
- [Lenco mobile-money transfer request/response](https://lenco-api.readme.io/v2.0/reference/initiate-transfer-to-mobile-money)
- [Lenco Zambia pricing](https://lenco.co/zm/pricing)

No payout code, provider configuration, actual balances or money-transfer state
was changed while preparing this draft.
