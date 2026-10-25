# Tenant rent collections and landlord mobile-money payouts

2026-10-25 implementation plan, following the user's clarified scope. Subscription
billing/pricing remains deferred. API documentation does not state that separate
approval is mandatory for this collection-then-transfer flow; account-specific
permissions, funding and limits remain to be exercised rather than assumed.

1. Persist rent collection attempts, immutable approved payout destinations,
   independent payout attempts and an append-only encrypted provider exchange
   history. Keep HTTP failures, malformed responses and network-error metadata;
   omit credentials and sensitive card fields. Protect payment tables with
   PostgreSQL default-deny RLS and revoke unrelated external-role grants.
2. Let linked tenants start hosted card/mobile-money checkout for their own
   invoice. Choose amount/currency/reference/destination on the server; require
   idempotency keys, mailbox/workspace access and online-payment entitlement.
   Scope tenant history to their own records and manager history to a workspace.
3. Verify collections via Lenco before changing the invoice ledger. Create one
   ordinary payment/receipt per successful attempt, updating existing balances,
   arrears and receipt APIs. Preserve paid-but-unallocated exceptions. Never
   downgrade success because of stale provider responses.
4. Authenticate webhooks against raw bytes, persist/deduplicate valid receipts
   and process via a worker, with periodic polling as a fallback. No external
   network request inside the initiating API's transaction.
5. Queue landlord payouts only for verified collections with settled funds in
   the configured debit account. Pay out the net settled amount; transfer fees
   are paid by the platform account and require additional available balance.
   Persist the destination and amount before sending. Submit each reference at
   most once; on timeout/crash poll that reference rather than repeat the debit.
   Track payout failure independently from the tenant's successful rent payment.
6. Add platform-only exchange inspection and reasoned destination approval;
   never expose provider credentials or internal response bodies to tenants or
   managers. Disable initiation/transfers by default until configuration is
   installed; test with mocked provider responses without moving live money.
7. Validate happy/failure/security paths, full backend suites and PostgreSQL
   locking/privileges. Use focused commits. New payment UI surfaces follow the
   existing Figma review requirement; no unreviewed redesign or deployment.

Official sources: [checkout](https://lenco-api.readme.io/v2.0/reference/accept-payments),
[collection verification](https://lenco-api.readme.io/v2.0/reference/get-collection-by-reference),
[mobile-money transfer](https://lenco-api.readme.io/v2.0/reference/initiate-transfer-to-mobile-money),
[transfer verification](https://lenco-api.readme.io/v2.0/reference/get-transfer-by-reference),
[webhooks](https://lenco-api.readme.io/v2.0/reference/webhooks).
