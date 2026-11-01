# Operational notice review fixes — 1 November 2026

Claude's source review found rollout, volume and business-write coupling issues. Work remains local: no provider signup, DNS, environment changes, live sends, payment implementation or deployment. The user subsequently authorized small local commits, scan failure isolation and consolidation of the unreleased migrations.

## Implementation against the review

1. Explicit scheduler registration; `APP_OPERATIONAL_EMAIL_ENABLED` defaults false. Pause skips email claims/attempts; seven-day expiry still applies. Operational/composed/beta emails carry a bulk marker through routed and SMTP-only transports. The final ten percent of each provider's daily/monthly allowance is reserved for account/security/signing mail. Locked reservations count failed/unknown attempts.
2. `APP_EMAIL_PROVIDER_ORDER` selects providers before I/O, supporting Resend primary and Gmail fallback. Resend uses its configured authenticated sender and preserves Message-ID/headers. Unknown sends never fall back. Free-plan defaults stay conservative until the purchased plan is configured.
3. Skip blank addresses, cancel changed-contact intents, expire queued/held email after seven days. Cleanup includes held/review metadata older than 90 days, at most 500 deliveries/tick; original financial/signing evidence is retained.
4. Remove payment-provider save hooks; keep their enqueue/render targets for Claude. Billing/lease/repair enqueue runs inside a savepoint and logs failure. A notice bug cannot undo the business write; successfully enqueued intents still roll back with their business transaction.
5. Operational outbox exclusively owns reminder email. Legacy scheduling keeps SMS/WhatsApp; already queued legacy reminder emails cancel before transport. `run_messages` no longer runs operational scheduling/dispatch.
6. Invoice-issued notices are tenant-only, including suppression of old manager rows at dispatch. No digest introduced. Explicit `actor`, known record authors and authenticated request-local context exclude self-notification. Context resets after each response and does not cache authorization. Automated/unattributed events retain their audiences.
7. Normalize SMS business phone numbers; compare shortcodes/alphanumeric sender IDs as plain text. Keep wrong-destination and callback-credential rejection.
8. Operational tenant phone delivery requires the same verified-number link as managers, an active linked account, and the tenant's current number. Settings consent alone cannot prove ownership. Existing composed/legacy reminder consent rules remain separate. Re-saving verified users' preferences preserves proof. Two-way SMS setup is required; required email remains available.
9. Eight random unambiguous uppercase letters/digits, hashed and bound to user/number/channel/ten-minute expiry. Support SMS shortcodes as pairing destinations. Keep authenticated completion and issuance throttling.
10. Watch `scheduled_for`-only repair saves; unchanged saves produce no new event.
11. Partition daily keyset cursors by source/timezone and reset on local dates. Hydrate at most twice the requested page size across zones/sources (maximum 1,000 records/tick). SQL-distinct timezone traversal is bounded to 600 names; invalid names are skipped. Two unused legacy global cursor rows may remain.
12. User/tenant outbox FKs use SET_NULL. Dispatch rejects orphaned recipients. Account deletion cancels pending/claimed rows before clearing the FK so an account-bound tenant notice cannot become accountless mail.
13. Keep unrelated pricing/cost/report/tenancy drafts outside commits. The user has now authorized small local commits; see the follow-up below.

## Payment handoff and signal audit

Claude has now wired explicit payment-service helpers for collection failure/review/expiry, payout outcomes and withdrawal transitions. Failed/expired attempts notify the tenant; collection review notifies managers. Successful collections use the billing receipt. Payout outcomes and withdrawal request/cancellation/outcomes notify managers; withdrawal provider-pending progress is silent and the requesting actor is excluded. These calls use the same savepoint protection and do not add model save hooks. Provider activation remains separate from code publication.

Source review of billing/leases/maintenance/imports/documents/payment services found no production QuerySet.update of the watched invoice/payment/lease/repair event fields. Lease activation/end bulk-updates unit occupancy and tenant status, which are not watched notice events. Payment worker bulk-updates next_check_at for retries, outside signal ownership. Future bulk status writes need explicit enqueue because update bypasses model signals.

## Rollout configuration (documentation only)

The user chose Resend Pro. Verify purchase/account allowance and authenticate the Dwella sender using the exact DNS records supplied by the provider before enabling delivery.

```dotenv
APP_EMAIL_ROUTING_ENABLED=true
APP_EMAIL_PROVIDER_ORDER=resend,google
RESEND_FROM_EMAIL=Dwella <notifications@dwella.properties>
RESEND_MONTHLY_LIMIT=50000
# Local rolling-day safety ceiling, independent of the provider plan's daily cap.
RESEND_DAILY_LIMIT=10000
APP_EMAIL_BULK_RESERVE_PERCENT=10
APP_EMAIL_MESSAGE_ID_DOMAIN=dwella.properties
# Keep disabled until an explicitly authorized rollout.
APP_OPERATIONAL_EMAIL_ENABLED=false
```

Set RESEND_API_KEY privately. Use provider order `resend` to disable Gmail fallback. Include `operational_messages` explicitly in APP_SCHEDULER_JOBS alongside intended existing jobs; preserve test redirection/allowlists. Apply `0009_operational_notifications`, the consolidated unreleased migration, including private-table restrictions. Adding credentials does not authorize provider activation or queue release. Paused notices older than seven days expire instead of creating a historical burst.

## Validation

- Full SQLite suite: **1,192 passed, 24 skipped** (`output/notice-fixes-full-sqlite.log`).
- Final SQLite affected modules after the appointment-only rescheduling follow-up: **197 passed, 6 PostgreSQL-only skips** (`output/notice-fixes-final-focused.log`). Moving an appointment away and back again is covered; `updated_at` is not assumed to advance on an appointment-only save.
- Full PostgreSQL suite: **1,216 passed** (`output/notification-final-postgres.log`). Final affected-module PostgreSQL follow-up after the appointment fix: **203 passed**, including worker/quota concurrency checks (`output/notification-postgres-final-focused.log`). The isolated loopback PostgreSQL server stopped successfully after both runs.
- Django check, Ruff and migration consistency passed. Frontend production build passed with its existing chunk-size advisory; no frontend source was changed in this review follow-up.
- History endpoint: **4 queries for a small response and 4 for a full page**, matching the prior measurement (`output/notice-fixes-history-queries.log`). This is a bounded history-read regression, not a production-load or broader event-write performance claim.
- Payment webhook commit-with-broken-enqueue regression passed. No payment implementation files were edited.

Tests use synthetic data/mocked transports; no real sends or transfers. Live inbox placement/DNS/provider acceptance still require a separately authorized integration check. No commit, push, deployment or provider activation performed.

## Follow-up: scan isolation and commit preparation

2026-11-01: User assigned only the scan isolation and migration/commit tidy-up follow-ups to Codex. Payment service wiring remains Claude-owned. Actor fallback and the two rollout prerequisites remain unchanged.

Each scanned invoice/lease now has a savepoint covering schedule calculation and enqueue. Invalid fields or enqueue/database errors roll back that record's partial intents and log source, target ID and timezone. The scan continues and persists its cursor past the bad record, including when the bad record fills the entire page. Operators can repair the logged record; the following local day's scan reevaluates it against that day's reminder/expiry rules. This does not create a separate retry queue for a skipped day's notice. No network calls or additional persistent polling rows are added. Savepoint overhead is bounded by the existing page budget; infrastructure failures outside the per-record boundary still fail the job for normal retry.

The unreleased migrations 0009–0011 are folded into **0009_operational_notifications**, directly after 0008. Final FK deletion behavior, recipient constraint, timezone cursor length and PostgreSQL RLS/assistant grant revocation are preserved. This is a pre-release consolidation, not an upgrade path for a database that applied the old temporary names. Fresh migration application, consistency and private-table protection are checked in the validation below.

Commit groups: schema/privacy; shared email routing/quota; operational outbox; event integration; verified phone endpoints/callbacks; history API; scheduler/reminder ownership; lifecycle/scan regressions; beta transport acceptance; frontend history; frontend phone settings; documentation. Unrelated cost/subscription/report/tenancy and business messaging proposal drafts remain outside these commits. Local commits only; no push or deployment.

Follow-up validation:

- Full SQLite: **1,206 passed, 25 skipped** (`output/notice-scan-full-sqlite.log`).
- Full PostgreSQL: **1,231 passed** (`output/notification-scan-final-postgres.log`), including the six invoice/lease bad-record regressions and the fresh-migration private-table security check. The isolated server stopped successfully.
- Django check, Ruff, migration consistency and frontend production build passed. The final working tree retains the actor fallback and existing rollout prerequisites.
- Concurrent Claude-owned payment files are excluded from these commits; separate payment implementation/review remains Claude's responsibility. No live sends, transfers, environment changes, push or deployment were performed.

## Integrated pre-push verification

The user subsequently authorized committing and pushing all remaining local items to `develop` after a fresh validation run. This includes Claude's four payment-notice files as their own commit and the remaining planning/cost documents as documentation-only drafts. Earlier payment-handoff and local-only status entries describe the preceding checkpoints; the current integrated verification is recorded in [Local changes validation](LOCAL_CHANGES_VALIDATION_2026_11_01.md). Actor fallback, rollout prerequisites, provider configuration and production deployment remain unchanged.
