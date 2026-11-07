# Manual landlord withdrawals

Drafted 2026-10-26 as a proposal; implemented locally the same day (Claude).
Figma: file `aHlQPzHBsvGR4rNoabRQyW`, page "Payments — Manual withdrawals · 26 Oct"
(node `261:106`). It supersedes the earlier payout-cadence frames on `227:106`.

## Direction (confirmed by the user)

- Keep Lenco. Tenants already pay collection fees through Lenco configuration;
  Dwella adds no collection surcharge.
- Landlords pay the payout fee, and withdraw when they choose. Automatic
  per-collection payouts are off unless `LENCO_AUTOMATIC_PAYOUTS=true`.
- The landlord enters the **amount they receive**. The fee is shown separately and
  **amount + fee** is taken from their balance.
- Receiving accounts can be mobile money or a bank account.

## Balance

Per workspace, in the database:

```
available = settled rent
          - legacy payouts (queued/submitting/pending/successful/review)
          - withdrawals in flight (amount + fee reserved)
          - successful withdrawals (amount + fee charged)
```

Pending collections are "awaiting settlement" and cannot be withdrawn. The pooled
Lenco account balance is never shown as the landlord's balance.

## Fees

Lenco publishes ranges, not an exact quote, so Dwella reserves the top of each
public band (`LENCO_WITHDRAWAL_FEES` in settings):

| Rail | Up to K1,000 | Up to K50,000 |
| --- | --- | --- |
| Mobile money | K12 | K25 |
| Bank account | K10 | K25 |

The transfer response reports the actual `fee`. The landlord is charged
`min(reported fee, reserved fee)`; any difference stays in their balance. A fee above
the reserve is recorded as `withdrawal_fee_above_reserve` for review (Dwella
absorbs it). A missing fee is charged at the reserve and flagged
`withdrawal_fee_not_reported`. Minimum withdrawal `LENCO_WITHDRAWAL_MINIMUM`
(default K10); maximum K50,000 per withdrawal. "Withdraw the maximum" accounts for
the fee band.

## Flow and safety rules

1. `POST /payments/withdrawals/preview/` returns amount, fee, total and balance
   after. It never contacts Lenco.
2. `POST /payments/withdrawals/` with amount, the previewed fee and an idempotency
   key. Under one workspace lock it rechecks membership, receiving account, balance
   and that the fee is still current, then saves a queued withdrawal. Repeating
   the same key returns the same withdrawal.
3. The worker claims the row (committed before any provider call), rechecks that
   the receiving account is still enabled and the requester is still a landlord
   (otherwise cancelled), waits while `LENCO_PAYOUTS_ENABLED` is off or the Lenco
   balance is not freshly matched, then sends **one** transfer
   (`/transfers/mobile-money` or `/transfers/bank-account`).
4. Timeouts and unclear answers are only ever checked by reference
   (`/transfers/status/{reference}`); a transfer is never sent twice. An outright
   refusal fails the withdrawal and returns amount + fee to the balance. A response
   whose reference, account or amount does not match goes to review.
5. Webhooks (`transfer.*`) update the withdrawal by reference. After 3 days without
   confirmation it goes to review.
6. Only a queued (unsent) withdrawal can be cancelled.

## Receiving accounts

- Mobile money (network + number) or bank (bank from `GET /payments/banks/`, a
  24-hour cached Lenco list, + account number).
- "Check account" asks Lenco for the registered name (`/resolve/mobile-money`,
  `/resolve/bank-account`). That name is saved; the landlord cannot type over it.
- Saving requires the landlord's password, the authenticator code when 2FA is on,
  and confirmation. An email is sent on every change. Withdrawals already sent keep
  their original account.
- Test bypass: only when `APP_ENVIRONMENT=test` and
  `LENCO_ALLOW_UNVERIFIED_DESTINATIONS=true` **and** Lenco cannot be asked, the
  landlord may type the name.

## API

| Method | Path | Purpose |
| --- | --- | --- |
| GET/POST | `/payments/destination/` | Receiving account (POST = change) |
| POST | `/payments/destination/check/` | Lenco name lookup |
| GET | `/payments/banks/` | Zambian banks |
| GET | `/payments/payouts/` | Balance summary, receiving account, limits |
| GET/POST | `/payments/withdrawals/` | History / request |
| POST | `/payments/withdrawals/preview/` | Fee preview |
| POST | `/payments/withdrawals/<id>/cancel/` | Cancel a queued withdrawal |
| GET | `/payments/platform/withdrawals/<id>/` | Super admin detail + evidence |

## Frontend

- `/billing/payouts`: balance strip, receiving account, Withdraw drawer with fee
  review, withdrawal history (cancel for queued rows). Linked from Billing.
- Receiving account drawer (Payouts and Settings → Billing): type, details, Check
  account, Lenco result, confirmation, password/2FA.
- Super admin Transactions: Withdrawals tab and drawer; legacy tab renamed
  "Automatic payouts".
- Manager alerts: withdrawal delivered / failed (returned to balance) / needs
  attention.

## Rollout checklist (test environment first)

- Migrate (`payments.0011`), keep the payments worker running.
- `LENCO_PAYOUTS_ENABLED=true`, `LENCO_AUTOMATIC_PAYOUTS` unset (false).
- The Lenco API key needs transfer permission (the earlier 403 blocker) and
  account-name resolution.
- Verify with a small real withdrawal on the user's own number before production.
