# Native mobile-money collection

2026-10-25: tenants enter a payment amount, their own mobile-money number and
network in Dwella. Cards retain Lenco hosted checkout, restricted to the card
channel. Existing hosted attempts remain resumable during rollout.

Use the existing tenant-scoped, throttled checkout endpoint and invoice lock.
Persist channel/payer details and a submission claim before requesting a debit;
commit the claim before the network call. Repeated keys and concurrent requests
must never send another mobile-money request. An uncertain response is checked
by reference using the existing worker/webhook path, never blindly resubmitted.
Keep provider request/response evidence in the existing protected evidence store.
No phone PIN or OTP is collected by Dwella. Payment confirmation, receipts,
allocation and automatic payouts use the existing verified ledger path.

Validate phone, operator, amount, ownership and channel server-side, mirror input
validation in the form, and block changing a pending attempt into another rail.
No network call under an invoice/collection lock. No additional polling loop.
Provider `pay-offline` means authorize on the phone, never paid.

Validate happy/failed/timeout/malformed results, immutable idempotency inputs,
unauthenticated/cross-tenant/manager access, throttling and concurrent claims;
run backend checks, Ruff/full suite, frontend build/Node checks and bounded mocked
browser checks. The notification badge fix must remain visible on desktop/mobile
and light/dark, preserving the existing popover and accessible unread label.

Official contracts:
- https://lenco-api.readme.io/v2.0/reference/initiate-collection-from-mobile-money
- https://lenco-api.readme.io/v2.0/reference/accept-payments

Deployment is test only, preserving test data and production. Validation must
not initiate live collections, payouts or messages; user performs real tests.

Implemented: persisted submission claims and immutable payer/channel reuse;
single bounded POST with retained evidence; normal verified receipts/payouts;
native form with inline validation and phone authorization status; card-only
hosted checkout. Pending native attempts remain status-only after a transport
error or reload. Provider success is checked against the saved payer and rail.

Validation: all payment tests passed locally (PostgreSQL-specific checks await
CI), Django check/migration consistency/Ruff passed, frontend build and 23 Node
checks passed. Mocked browser checks covered invalid input, exactly one native
request/no hosted script, reload while pending, verified receipt transition,
card-only widget/cancel/resume, and unclipped 99+ badge with keyboard popover
access at desktop/mobile sizes in light/dark. Full local backend rerun uses a
dedicated temporary folder after Windows denied the default pytest directory.

| Before | After | Why |
| --- | --- | --- |
| Mobile money opened the hosted widget | Immediate request/phone-authorization feedback in Dwella | Keeps the tenant oriented without another popup |
| Badge could be clipped by the button | Visible overflow and badge stacking above the border | Keeps unread count legible without altering header layout |

Existing Fluent progress indicators are reused; no custom motion, success timer
or additional polling loop is introduced.
