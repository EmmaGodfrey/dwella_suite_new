# Lenco payment integration: initial setup

Reviewed 2026-10-25. The user confirmed the keys are live and authorized using
that account. Live API authentication is verified. Collection, payout and webhook
flows are still unimplemented; nothing has been deployed for this integration.

## Current setup

Public and secret/API keys were entered in a hidden-input PowerShell window and
saved only to the protected local root `.env`:

- `LENCO_ENVIRONMENT=live`
- `LENCO_LIVE_PUBLIC_KEY`
- `LENCO_LIVE_SECRET_KEY`
- `LENCO_PAYMENTS_ENABLED=false` (reserved configuration; no collection
  implementation exists yet).

Do not put the secret in Vite variables, browser responses, logs, tracked files or
command arguments. Keys have not been installed on the server. The original
sandbox key-entry helper under ignored `output/` is not suitable for reentering
live credentials; do not rerun it for this live setup.

From `backend/`, run the read-only diagnostic:

```powershell
.venv/Scripts/python.exe manage.py check_lenco --environment live
```

The explicit environment must match `LENCO_ENVIRONMENT`. Each environment uses
only its matching secret. The client sends one GET, with TLS verification, a
timeout, bounded JSON parsing and no redirects or environment fallback. It
prints only a count or a safe error and never initiates a payment or transfer.
The live resource is the documented
[v2 accounts endpoint](https://lenco-api.readme.io/v2.0/reference/get-accounts).

Actual result on 2026-10-25: live authentication succeeded; one account record on
the first page. Account details and balances were not printed or persisted. This
does not prove card/mobile-money rail activation, the public checkout key,
webhook delivery or a successful collection. An earlier sandbox check with these
keys returned HTTP 401 before the user clarified their environment.

A sandbox option exists, using separately named `LENCO_SANDBOX_SECRET_KEY` with
`LENCO_ENVIRONMENT=sandbox`. Its v2 URL combines the documented sandbox hostname
with the v2 resource and still needs provider confirmation. The documented sandbox
checkout script failed TLS negotiation from this machine. Neither sandbox
collections nor browser checkout were verified; do not bypass TLS checks.

## Agreed implementation direction

Use Lenco's [hosted checkout](https://lenco-api.readme.io/v2.0/reference/accept-payments)
for mobile money and cards, with only the public key in the browser. Dwella must
never collect card PAN/CVV. Amounts use major currency units, represented with
Decimal in Dwella. The server chooses the invoice, amount, currency and unique
reference; the browser cannot supply an authoritative paid amount.

The [API authentication guide](https://lenco-api.readme.io/v2.0/reference/get-started)
requires HTTPS Bearer authentication. HTTP 200 or a checkout callback alone does
not mean rent was paid. Recheck the
[collection by reference](https://lenco-api.readme.io/v2.0/reference/get-collection-by-reference)
on the server and validate reference, amount, currency and workspace/invoice
ownership before recording a payment.

Add a separate provider payment-attempt lifecycle to preserve pending, successful,
failed and reconciliation-required outcomes. Retain the existing manual payment
flow. Provider success must be deduplicated transactionally and produce one
receipt. An already-paid or voided invoice must place received money into a
reconciliation exception rather than discard the provider outcome. Avoid holding
database locks across network requests.

For [webhooks](https://lenco-api.readme.io/v2.0/reference/webhooks), validate
`X-Lenco-Signature` with constant-time comparison over the exact raw request
bytes. The documented signing algorithm is HMAC-SHA512 using the hex SHA256 of
the API token as the key. Verify a real sandbox sample before relying on this
contract. Persist a bounded receipt, deduplicate/reconcile asynchronously and
acknowledge quickly; handle retries and out-of-order events. Poll status as a
fallback. Keep successful collection separate from settled funds.

Managers see their own destination, fees, net amounts and settlement status from
[provider settlement data](https://lenco-api.readme.io/v2.0/reference/get-settlements),
never API credentials. Tenants see only their own invoices and attempts. Provider
configuration stays platform-admin controlled. New sensitive tables need explicit
PostgreSQL privileges and RLS protections against unrelated external DB roles.

## Before live rent collection

Confirm with Lenco how Dwella's separate property managers are onboarded and how
their settlement destinations are assigned. The reviewed checkout parameters do
not establish a split-payment/submerchant arrangement. Do not infer that one
Dwella merchant may receive every manager's rent or invent automatic payouts.
Confirm Zambia rail activation, actual fees, fee bearer and settlement schedules
for this account.

Next implementation slices: attempt model and
permissions; initiation and authoritative reconciliation; signed webhook receipt
and polling; scoped status/receipt APIs; approved tenant checkout UI. Exercise
[sandbox fixtures](https://lenco-api.readme.io/v2.0/reference/test-cards-and-accounts),
duplicates, tampering, amount/currency mismatch, permission failures, timeout,
out-of-order events and manual-payment races before deployment. Autopay,
automatic bank matching, refunds and payouts remain outside this initial scope.

Validation for this slice: Django system check and repository Ruff checks pass;
57 integration tests pass, including 28 Lenco tests for environment selection,
credential validation, redacted failures, redirects, timeouts and malformed
responses. The live smoke check was read-only; no collection test has been run.
