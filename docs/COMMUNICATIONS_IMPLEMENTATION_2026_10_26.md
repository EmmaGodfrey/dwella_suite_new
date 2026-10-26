# Send-only communications implementation

User authorised 2026-10-26: scheduled email/SMS/WhatsApp reminders, reminder
settings, explicit on-demand messages and Handy actions; connect provider APIs
later. Also release Settings/Transactions to test and fix removed tenant access.
Payout changes are deferred; user says collection fees are configured in Lenco.

## Plan and boundaries

- A manager selects up to 100 workspace tenants, channel, subject and plain text;
  preview freezes recipients/content for 30 minutes. Confirmation submits that
  exact preview once. Cross-workspace or changed recipients are rejected.
- Keep per-recipient delivery records, with held/queued/sending/sent/failed/
  cancelled/review states. Held is not sent. Connecting APIs must not release old
  held notices without explicit review. No inbound chat or conversation model.
- All new external delivery is off by default. Email uses the existing guarded
  Django backend only after an explicit environment enable. SMS/WhatsApp have no
  send adapter yet. Phone opt-in/template/callback activation stays blocked.
- Reminder settings can be saved before connecting providers. Schedule rent
  reminders before/on/after invoice due dates; deduplicate each invoice/date/
  channel. Use bounded scans with a durable cursor, then recheck current invoice,
  workspace, contact, consent/preferences and permissions before dispatch.
- No provider/SMTP call inside a transaction. Claim before send; uncertain sends
  go to review rather than automatic retry. Respect quiet hours and spending
  holds. Do not claim provider delivery from SMTP acceptance.
- Handy uses its existing short-lived, freshly authorised action boundary for
  preview and separate confirmation. Confirmation is documented as requiring
  the user's explicit approval of that preview, with stable idempotent identity.
- Access removal records the account's former tenant access. An unassigned former
  tenant gets an access-removed screen and cannot enter business setup; a fresh
  valid invitation restores access. Do not reactivate suspended memberships.

## Design references

Approved settings review page 233:9669, extended with editable Figma references:
Messages/history 256:106; compose 256:115; review 256:124; removed access 256:133.
Use existing table, drawer, Fluent field and status components.

## Validation

Cover unauthenticated/tenant/foreign-workspace/expired-preview/malformed/throttled
requests, duplicate confirmation, changed recipients, workspace suspension,
paid invoices, deduplicated schedules, provider holds, no-send defaults, stale
claims, permission revocation, former-tenant setup denial and invitation recovery.
Compare list/preview query counts at small/full sizes. Run Django check, Ruff,
full backend suite and frontend build, then browser flows and CI/test deployment.

## Implemented behavior

- Manager `/messages`: search/filter/paginate request history, compose for up to
  100 selected tenants (recipient search and pagination), review exact contacts
  and content, confirm once, inspect content/status, cancel a held/queued request.
- Admin `/admin/messages`: workspace-labelled delivery history and failure/hold
  reasons. `/admin/transactions` retains the separate payment evidence browser.
- Settings > Notifications: save email/SMS/WhatsApp preferences before connecting
  providers. Tenant reminder schedule covers before due date, due date, repeat
  interval and a bounded number of overdue notices, at the workspace local hour.
- Admin Settings > Messaging: global schedule switch and quiet hours. SMS fallback
  stays unavailable. Monetary caps are saved for future paid adapters; SMS and
  WhatsApp currently cannot send at any cap. Current Gmail SMTP has no integrated
  per-message debit; do not claim spending accounting for a future paid provider.
- `run_messages` schedules up to 200 candidate invoices per run using a persistent
  cursor, deduplicates invoice/date/channel, then considers up to 50 queued
  deliveries. Dispatch has a 45-second budget checked between attempts and a
  maximum 10-second SMTP timeout per attempt. Quiet notices are deferred until
  the quiet period ends. No catch-up burst of previous-day reminders is sent.
- `APP_SCHEDULER_JOBS=...,messages` enables the existing scheduler's five-minute
  job. Global reminders and workspace channels default off. Explicitly enable
  `APP_MESSAGING_EMAIL_ENABLED=true` only after sender/recipient review. Existing
  account/signing mail is unaffected. SMS/WhatsApp have no configured adapter.
- Held requests never auto-release when a provider is connected. For this phase,
  cancel/recompose after reviewing a held message to make a new sending request.
  Provider callbacks, WhatsApp opt-in/approved-template activation and phone
  delivery evidence belong to the later API attachment; none is simulated here.
- Status `sent` means SMTP accepted the message, not confirmed inbox delivery.
  Timeouts/crashes after claim become `review`; the worker never blindly retries.
- Backend rechecks workspace/actor authority, features, current contact and
  recipient channel preference. Rent reminders also recheck payment/void state,
  enabled schedule and current local date, and refresh partial-payment balances.
- Private message tables use PostgreSQL default-deny row security and revoke the
  external Handy database role. Handy accesses messages through two new marked
  OpenAPI actions (11 total), not SQL. Refresh the provider's imported schema and
  knowledge package when attaching the integration; no provider upload was made.
- Account removal sets `AccountAccessState.tenant_access_removed`. Unassigned
  former tenants cannot enter workspace setup, and the frontend explains how to
  request a fresh invitation. Accepting a valid new invitation clears the flag.
  Admin user projections use prefetched state and preserve constant query counts.

Preview/confirmation use at most one recipient lookup for the whole selection;
history loads related names in one query and omits message bodies until detail.
Regression checks compare 1/25 recipients and 1/25 delivery rows. These are query
budgets, not a load/capacity claim for the current VPS. Per-recipient history is
meaningful user evidence; duplicate polling snapshots are not persisted.

## Local validation completed

2026-10-26: Django check, migration consistency and Ruff passed. Final full SQLite
suite: 935 passed, 18 skipped (PostgreSQL-only cases run in CI). Frontend production
build and 25 existing Node checks passed. Synthetic browser checks passed compose,
exact review, no confirmation before review, failed-confirmation retry without a
new preview, held history, saveable unconnected preferences and removed-access
feedback at desktop/mobile and light/dark. Screenshots are private under
`output/playwright/messages-*.png`. No live notice, charge or transfer was sent.

The first full run caught query regressions in admin user projection; those were
fixed by passing prefetched access state into the display projection. Final
regression tests pass. Initial worker checks also found new-instance quiet-hour
type conversion, now fixed. No unexplained validation failures remain locally.
CI PostgreSQL verification and test deployment are the next release checks.

## Verified test release

2026-10-26: code through `bf4dfb0` deployed as `test-v2026.10.26.1` through successful
[CI run 40355075224](https://github.com/EmmaGodfrey/dwella_suite_new/actions/runs/40355075224).
Full SQLite, expanded PostgreSQL, frontend and staging-deployment gates passed;
the production deployment job was skipped. Live test checks confirm current
migrations, three private message tables, protected admin APIs, eleven marked
Handy actions and a successful `messages` scheduler run. New outbound delivery
is disabled; SMS/WhatsApp APIs remain unattached. Production container identities
match the saved pre-release baseline.

The deployed browser build passed the send-only message flow, partial-save retry,
reminder choices, role-specific settings, transaction evidence on demand, mobile
and dark states, and removed-tenant screen using intercepted synthetic API data.
No real message, payment or transfer was initiated by these checks. The read-only
verification script initially needed its quoting and HTTPS request setup corrected;
the deployed application checks now pass. Research/subscription proposal documents
were excluded from this application release.
