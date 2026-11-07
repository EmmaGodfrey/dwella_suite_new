# Transactional notifications

**1 November follow-up:** [Claude review fixes and rollout settings](OPERATIONAL_NOTICE_REVIEW_FIXES_2026_11_01.md) supersede the original rollout/coverage details below. Operational email now defaults off; the scheduler job must be explicitly listed. Invoice-issued mail is tenant-only and known actors are excluded. Payment-provider save hooks have been removed; Claude's payment services now use explicit notice helpers. Notification enqueue failure is isolated from business writes. Apply the consolidated unreleased migration `0009_operational_notifications`; it replaces the former 0009–0011 chain before first release. Earlier validation results below describe the 31 October implementation; use the follow-up and [integrated pre-push validation](LOCAL_CHANGES_VALIDATION_2026_11_01.md) for current validation.

2026-10-31: User authorised mandatory operational email across modules, optional SMS/WhatsApp and refreshed cost calculations. Implementation stays local pending release; the separately authorised production task is one beta welcome resend.

## Plan

- Persist deduplicated notification intent with domain changes, dispatch after commit through a bounded database outbox. Existing money operations and balances remain authoritative. No SMTP/network work in domain transactions.
- Cover invoice creation/void, confirmed/corrected payments, lease activation/end/signature status and expiry, maintenance requests/status/public comments, failed collections and payout/withdrawal outcomes. Existing account/signing mail stays separate to avoid duplicate emails.
- Send mandatory operational email to current eligible managers and the relevant tenant. Ignore optional email switches for these events and scheduled operational reminders; preserve test allowlists and provider quotas. Do not turn on live providers during development.
- Optional SMS/WhatsApp use personal opt-in and exact-number consent. Manager numbers require a signed inbound account-pairing challenge; email remains usable without optional channels. Receipt messages link to authenticated Dwella pages rather than attach private PDFs to SMS.
- Reuse the existing scheduler/provider transports. Retry only known safe local/quota failures. Unknown external outcomes require review. Deduplicate recipient/event/channel, recheck current authority/contact before dispatch, restrict private tables from direct assistant access, paginate delivery history, and bound scheduled scans/retention.
- Validate rollback/idempotency, recipient isolation, stale/revoked memberships, private repair comments, opt-outs, malformed pairing, throttling, quotas, retries and uncertain sends. Measure small/full list queries, run Django/Ruff/migration checks, full backend tests and frontend build/sanity checks.

No in-place model switching is exposed in this runtime; plan, implementation and validation are kept as separate stages. Existing payment ownership is respected by putting event observation in notifications rather than rewriting provider/accounting logic. User explicitly authorised this cross-module notification work.

## Implemented coverage

| Trigger | Required email audience |
| --- | --- |
| Invoice issued/cancelled | Current managers and subject tenant |
| Payment confirmed or manual payment corrected | Current managers and subject tenant; only confirmed billing payments, never an unverified checkout redirect |
| Lease awaiting signature, activated or ended | Current managers and subject tenant; superseded unsent states are suppressed |
| Lease expiry milestones | Current managers and subject tenant; 30-day, seven-day and expiry buckets, deduplicated by end date |
| Repair reported, assigned/scheduled/rescheduled, started, completed/cancelled | Current managers and relevant tenant; current status and appointment time, no internal costs/access notes |
| Public repair comment | Current managers and relevant tenant; internal notes never create a tenant email |
| Failed/expired/review collection attempt | Current managers and subject tenant; explicitly says payment is not confirmed |
| Withdrawal requested/processing/delivered/failed/review/cancelled | Current managers; stale intermediate states are suppressed |
| Legacy collection-linked payout delivered/failed/review | Current managers; tenant payment remains recorded |
| Rent due reminders | Subject tenant, using the existing workspace lead/due/overdue dates, even when optional channels are disabled |

Existing mailbox verification, password recovery, tenant invitation, signing invite/code/completed-PDF and receiving-account-change mail paths remain. Identity-review readiness now uses the shared transport check rather than matching a backend name for “smtp”. Those existing account/security paths are separate from the operational outbox; this change does not turn them into optional paid outreach.

## Delivery and access rules

- Event observation lives in notifications signals; domain services that already transact financial/lifecycle writes keep the outbox insert in that transaction. No provider/accounting rules or cash balances were rewritten. New unauthenticated/public event mutation APIs were not introduced.
- Required operational email bypasses personal email opt-out, optional messaging feature policy and the optional-notices runtime switch. Transport readiness, quota reservation and test allowlists still apply. Missing/changed email addresses are held with a visible reason rather than silently redirected to another recipient.
- Managers must remain active, mailbox-eligible workspace members; tenant user linkage and current contact/object scope are rechecked before delivery. A removed manager or reassigned tenant never receives queued private notices.
- Operational email is scheduled every five minutes through the existing scheduler as a required job. `APP_SCHEDULER_JOBS` still controls optional jobs. Deploying this code introduces required operational mail without requiring the optional `messages` job. Test recipient guards remain in force.
- `run_messages` also invokes the operational stages for manual compatibility. Unique identities and atomic claims prevent duplicate dispatch when both entry points overlap. Old optional rent-email scheduling recognises required email already queued for that invoice/date.
- Known quota/readiness failures wait; uncertain SMTP/network outcomes go to review and are not blindly resent. Stable Message-ID aids investigation but is not a guarantee of inbox placement or provider idempotency. A send failure does not reverse a payment or repair action.
- Optional SMS/WhatsApp require opt-in, live feature/provider configuration and exact-number consent. Managers use signed inbound verification plus completion from their authenticated account. Pairing expires after ten minutes, is rate limited, stores only a token digest and cannot be completed by another user.
- Receipt/invoice phone messages carry summaries and authenticated Dwella links. No receipt PDFs, ID documents or payment-proof images are exposed as public URLs. Optional notices expire after three days; required email stays visible if held.
- WhatsApp free-form operational replies require that recipient's open service window. Outside it, an approved dedicated operational template is required; a rent-reminder template is not reused for receipts. Delivery status in operational history currently records transport acceptance/failure/review; this does not assert a handset read or inbox delivery.
- A bounded daily keyset scan schedules reminders/lease milestones. Each row has its own due time, so a workspace choosing a later hour cannot block another workspace's page. Operational delivery metadata is retained 90 days; expired pairing metadata seven days. Financial/signing evidence is unaffected.

## Configuration and release

No production/staging release, bulk-email activation or provider setup was performed. The only authorised production mutation was the separately requested single beta welcome resend; its contact/result are recorded privately rather than in tracked documentation.

Before releasing:

1. Apply notifications migration `0009_operational_notifications`, including PostgreSQL RLS/direct-assistant restrictions, then deploy backend/scheduler before frontend.
2. Confirm the existing SMTP transport, verified sender, quotas and environment recipient guards. Required emails are operational, not marketing; keep unsubscribe/optional outreach preferences separate. Validate with synthetic recipients first.
3. For WhatsApp, set `APP_WHATSAPP_PUBLIC_NUMBER` to the actual business number and `APP_WHATSAPP_OPERATIONAL_TEMPLATE` to an approved template whose three body parameters are subject, summary and authenticated link. Allowlist template/language through the existing approved-template configuration. Keep the existing access token/app secret/number ID in protected environment configuration.
4. For SMS pairing, set `APP_SMS_INCOMING_NUMBER` only when the provider supplies a genuinely two-way route; an alphanumeric sender ID alone cannot receive a CONNECT reply. Preserve the existing callback-token and sender-registration checks. Outbound-only SMS remains available for existing consented tenant contacts.
5. Optional providers remain off until explicitly configured/enabled. The phone-link UI reports unavailable channels without sending an unsolicited verification message or changing a tenant's mobile-money wallet.
6. Review **Messages → Operational updates** for held/failed/unknown outcomes, independently of manually composed notices. Workspace history is scoped/paginated; platform history is super-admin only. Never blindly reset an unknown send to queued. Investigate accepted emails using sender/provider evidence; an SMTP acceptance row is not a delivery receipt.

Email capacity is a release constraint: an invoice email to one tenant and one manager across 700 units is 1,400 recipient deliveries before payment confirmations/reminders. The existing shared SMTP quota may intentionally defer that workload over several days. “Required” means an event always queues email and cannot be disabled by an optional preference; it cannot bypass the sender's quota or guarantee immediate inbox placement. Confirm appropriate transactional-mail capacity before onboarding that portfolio, rather than raising a Gmail cap beyond its real allowance.

Cost/allowance recommendations are in `MESSAGING_COSTS_AND_ALLOWANCES_2026_10_31.md`. No credit wallet, subscription prices or top-up charges were implemented.

## Validation record

- Django system check, Ruff and migration drift check passed during implementation.
- Notification-history query measurements: four queries for a small response and four for a full page; no per-recipient row growth. Broader event/write cost and external delivery latency are not production load-test claims.
- Synthetic browser flow passed desktop and 390-pixel mobile: required email controls, invalid phone prevention, consent, code handoff, authenticated completion and operational/manual history switch; zero JavaScript page errors and no settled mobile overflow. API/phone-provider responses were mocked, not live sends.
- Frontend production build passed. Full SQLite/PostgreSQL and final follow-up results are recorded below.

Final validation on 2026-10-31:

- Full PostgreSQL suite: **1,194 passed** (`output/notification-final-postgres.log`). Follow-up after the final scheduling/comment transaction changes: **192 passed**, including concurrent worker claims (`output/notification-postgres-final-focused.log`). Own loopback PostgreSQL instance shut down after each run.
- Final full SQLite suite: **1,172 passed, 24 skipped** (`output/notification-release-sqlite.log`). Skips include PostgreSQL-only concurrency/locking checks covered by the PostgreSQL runs.
- Beta-email transport acceptance fix: **26 passed** in its follow-up module suite (`output/notification-beta-acceptance.log`). This additional regression ensures a zero-return transport does not leave a welcome marked sent. Historical sent rows still cannot prove inbox placement; the production resend was separately observed returning one accepted email.
- Final Django `check`, migration drift check, Ruff and diff whitespace check passed. Frontend production build passed with the existing large-chunk advisory. Browser tests used synthetic accounts/API responses; no real payment, SMS, WhatsApp or extra welcome email was sent by validation.
- The manager repair-comment action now explicitly wraps the comment and notification intent in one transaction; the rollback regression passed on SQLite and PostgreSQL.
- Browser and task Vite server closed; temporary validation services stopped. No commit/push/deployment or provider activation performed. Unrelated existing pricing/report/tenancy-operation work remains untouched.

Suggested focused commit boundaries: notification schema/privacy; event/outbox and atomic comment integration plus tests; optional phone connection/API; scheduler and reminder deduplication; frontend settings/history; beta acceptance correction; documentation/cost model. Keep the existing unrelated cost/subscription edits out of these commits.
