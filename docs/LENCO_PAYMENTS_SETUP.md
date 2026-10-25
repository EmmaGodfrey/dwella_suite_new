# Lenco rent payments

Updated 2026-10-25. Tenant checkout, server verification, receipts, immediate
mobile-money payouts, private response history and balance reconciliation are
implemented locally. Nothing in this payment integration has been deployed or
activated. Subscription billing remains deferred.

## Implemented flow

1. A linked tenant opens their own invoice and chooses a partial or full amount.
   The server fixes the reference, currency, amount and approved landlord
   destination; an idempotency key prevents a repeated request creating a debit.
2. Lenco's hosted widget collects mobile money/card details. Dwella never handles
   card PAN/CVV. Its callbacks only queue a server check, never mark an invoice
   paid. Pending attempts can resume with the same reference.
3. The worker fetches the collection by reference and checks identity, currency
   and amount. A successful collection creates one ordinary billing payment and
   receipt, updating invoice balances, arrears, tenant totals and notifications.
   A void/manual-payment race preserves received money as a reconciliation
   exception instead of crediting twice or losing the provider result.
4. When the net funds settle into the configured account, a payout is queued to
   the immutable approved phone/operator. Payout is submitted only with a fresh,
   matching balance snapshot and sufficient unreserved available balance. The
   claim commits before the HTTP request. A crash, timeout or ambiguous response
   causes status polling of that reference, never a second POST/debit.
5. Payout delivery/failure is separate from rent payment. A failed payout does not
   undo the tenant's payment. Managers see collection/settlement/payout states in
   the invoice, plus payout failures in their notification bell.

Collection fees reduce the landlord's settled principal. In this first flow the
platform account covers the separate payout fee and needs its own fee float.
Payout requests use the actual settled net, not an invented fee estimate. Pending
and recent completed payout principal/known fees reserve the reported balance
until the next comparison. Fee policy for period batches is still a design
choice; SaaS subscription prices have not been selected.

## Responses and financial records

Every provider request retains its timestamp, operation, HTTP status, safe error
category, original response digest and encrypted/redacted JSON response. Failed
HTTP responses, network failures, invalid JSON and oversized bodies are recorded.
Arbitrary non-JSON text is represented by a safe byte-count/digest diagnostic,
not retained verbatim. Credentials, authorization headers, OTP/PIN and sensitive
card fields are excluded. Valid webhook bodies are retained with duplicate
protection; bad signatures do not create evidence.

Evidence and financial snapshots are append-only in PostgreSQL. Payment tables
have default-deny RLS and unrelated external-reader grants are revoked. Only
platform superusers can inspect decrypted evidence; access is audited. Tenants
never receive internal provider bodies or landlord receiving details.

The read-only balance import copies every advertised transaction page, dedupes
provider IDs and preserves changed/missing-row discrepancies. It freezes an
opening baseline once, then compares:

- opening balance + imported credits - imported debits against Lenco ledger;
- a separate opening application position + settled rent - confirmed payouts
  and actual payout fees against Lenco ledger.

Available and ledger balances remain distinct. Incomplete pagination/data is not
labelled matched. External top-ups, withdrawals, unallocated receipts, provider
charges or an in-flight collection/payout can produce a discrepancy requiring
review or a later sync. The opening baseline is not proof of historical accuracy
and is never silently recalculated to hide a difference.

## Configuration and operational readiness

Secrets live only in the protected root environment file (server installation
will use its protected deployment environment file):

```dotenv
LENCO_ENVIRONMENT=live
LENCO_LIVE_PUBLIC_KEY=<public checkout key>
LENCO_LIVE_SECRET_KEY=<secret API token>
LENCO_DEBIT_ACCOUNT_ID=<verified ZMW account UUID>
LENCO_EVIDENCE_KEY=<dedicated Fernet key>
LENCO_EVIDENCE_KEY_FALLBACKS=
LENCO_PAYMENTS_ENABLED=false
LENCO_PAYOUTS_ENABLED=false
```

Keep the evidence key and retained fallback keys with protected recovery secrets;
backups containing encrypted responses require those keys. The original ignored
sandbox key-entry helper must not be reused for live keys. No secret belongs in
Vite variables. A public key is supplied only by the scoped checkout API.

Run from a configured backend environment:

```powershell
python manage.py check_lenco --environment live
python manage.py sync_lenco_finances
python manage.py process_lenco_payments
```

The first balance sync establishes a baseline; a later sync must be "matched"
before a payout can be submitted: Lenco's own history adds up exactly, and the
ledger covers the rent still owed to landlords. Money above that is reported as
surplus and does not block payouts. Payout fees are paid from that surplus, so
keep a small float in the collection account or payouts stop with "shortfall". The sync/check commands are read-only
with respect to Lenco. `process_lenco_payments` can move money only when the payout
switch is explicitly enabled and all guards pass. Never run it as a live debit
connectivity test.

At deployment, migrate the database; install the protected configuration; configure the public webhook URL
`/api/v1/payments/webhook/` in Lenco Pay; verify delivery and controlled collection/
payout behavior; then enable the chosen switches.

Managers enter receiving details under **Billing → Receiving details**. There
is no routine admin approval. SMS/WhatsApp ownership verification is not yet
configured. For the explicitly authorised test flow only, set
`APP_ENVIRONMENT=test` and `LENCO_ALLOW_UNVERIFIED_DESTINATIONS=true`. Both are
required; the bypass defaults off. It lets an authenticated active landlord
save a confirmed mobile-money wallet without a code and records an audit event.
The screen does not claim the phone is verified. Production must not enable
this bypass. No bank/card destinations or scheduled/manual payouts are exposed.
Existing collections retain the destination captured when checkout began.

The `payments-worker` service (`python manage.py run_payments_worker`) does the
checking, separately from the scheduler. It asks Lenco only about rows that are
due: a checkout every 30 seconds at first, slowing with age and expiring after
30 minutes unpaid; a settled collection or finished payout is never polled
again. It reconciles the balance every five minutes, importing only recent
transactions. A repeated identical Lenco answer is not stored again, a balance
record is written only when the outcome changes, and the worker writes no
per-run rows. Its heartbeat appears on the scheduler status.

The reviewed [getting-started](https://lenco-api.readme.io/v2.0/reference/get-started)
and [payout](https://lenco-api.readme.io/v2.0/reference/initiate-transfer-to-mobile-money)
pages do not state that separate provider approval is mandatory for this flow.
Account-specific payout permission, fees/limits and actual delivery are still
unverified; a successful account read does not prove a transfer works.

## API surface

All paths below are under `/api/v1/payments/`, with the existing response envelope,
authentication, mailbox/workspace checks and private/no-store headers.

| Endpoint | Purpose |
| --- | --- |
| `GET tenant/options/` | Whether online payment is available for this tenant's workspace |
| `POST tenant/invoices/<invoice UUID>/checkout/` | Amount + UUID idempotency key; server checkout configuration |
| `GET tenant/collections/?invoice=<UUID>` | Own attempt history/status |
| `GET/POST tenant/collections/<UUID>/` | Own status / queue authoritative verification |
| `GET collections/?invoice=<UUID>` | Manager workspace collection, fee and payout history |
| `GET destination/` | Manager's approved destination |
| `POST platform/destinations/<workspace UUID>/` | Superuser approval: phone, operator, holder name and reason |
| `GET platform/collections/` | Platform collection monitoring |
| `GET platform/collections/<UUID>/exchanges/` | Evidence metadata, paginated |
| `GET platform/exchanges/<UUID>/` | Audited decrypted/redacted evidence |
| `GET platform/balance/` | Latest private account comparison and Dwella totals |
| `POST webhook/` | Raw-body HMAC-SHA512 signature, durable receipt and fast acknowledgement |

Checkout/status writes are limited to 30/hour per user. Webhooks have a separate
600/minute source limit. Hosted callbacks are rechecked on the server; periodic
polling handles missed webhooks. Provider calls use verified TLS, fixed approved
hosts, bounded reads, timeouts, no redirects and no environment fallback.

## Bank payouts, held funds and review designs

Lenco documents bank-account payouts and its live Zambia bank directory returned
22 institutions in the read-only check. No card-payout endpoint was found.
Bank destinations and scheduled/aggregated/manual withdrawals are **designed,
not implemented or active** in this first immediate mobile-money flow.

Review the [new payout designs](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=227-107):
desktop drawers for mobile money (227:113) and bank accounts (227:214),
monthly (232:106) and manual hold (232:243), held funds/request payout (232:380),
landlord history (227:315), platform reconciliation (227:423) and the phone
form (227:514). Examples are illustrative.
Proposed timing is immediate/weekly/monthly/manual. Implement period batches and
separate landlord liabilities/reservations after the design is agreed; do not
expose pooled platform cash as a landlord's spendable balance.

## Validation

Full PostgreSQL suite: 782 passed. Full SQLite suite: 770 passed, 12 skipped.
Additional focused tests cover concurrent account reservations, eventual webhook
status visibility, immutable financial records and failed/invalid response
capture. Frontend production build and 19 Node tests pass. Browser checks with
synthetic data and a mocked provider widget covered invalid amounts, tampered
callbacks remaining pending, verified receipt/balance refresh, failure without
credit, manager settlement/payout delivery, mobile layouts and both themes.
No live collection or transfer was initiated.

Live read-only checks authenticated the account, retrieved the Zambia bank
list, imported one existing provider transaction and recorded a baseline followed
by a matched comparison. Actual response copies are retained privately/encrypted;
no balances, account names or credentials belong in tracked validation artifacts.
This does not constitute a live payment acceptance test.
