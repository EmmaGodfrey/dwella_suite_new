# Open repairs and tenant notifications

User authorised these two remaining MVP items on 2026-10-26. Preserve the existing
dashboard/Maintenance layouts and notification bell. No provider activation,
payment-flow changes, new chat platform or production deployment is included.

## Plan

- Add an organisation-scoped database aggregate for open repair requests to the
  existing dashboard response. Show the count, urgent/unassigned context and a
  link to Maintenance filtered to open requests. Refresh after maintenance writes.
- Reuse the existing notification endpoint/bell for tenants, authorised through
  `portal_context`, including fresh active tenancy, workspace and feature checks.
- Tenant sources: current unpaid invoices, recent payments/reversals, active lease
  endings, issued/signed lease documents, repair progress and non-internal updates.
  Link only to existing tenant routes. Never return internal comments, contact or
  identity records, manager finances, signing secrets or another tenant's data.
- Build a bounded live feed from existing indexed records; no per-poll event
  inserts. Stable event keys preserve read state; new visible repair updates have
  new keys. Keep source/read lookups bounded and query counts independent of rows.
- Validate mark-read IDs against the caller's current feed, limit/throttle writes,
  and retain mandatory overdue reminders when optional categories are disabled.
- Validate auth, ownership, unlink/archive/suspension, feature removal, internal
  notes, new update/read state, account/record isolation and small/full query count.
  Run full backend validation for shared permission behavior, frontend production
  build and focused browser checks on desktop/mobile/light/dark and error states.

Model switching is unavailable in this session. Follow plan, implement, validate
with the current model. The UI extends the existing approved surfaces; focused
editable reference frames are on Figma Settings & communications page 233:9669.

## Implemented and validated locally

- Dashboard `repairs` contains open/urgent/unassigned counts from one aggregate
  query, using active requests and the current workspace. Needs attention opens
  `/maintenance?open=true`. The existing board/list is retained, with an Open
  requests filter and a working Clear filters action. Maintenance writes already
  invalidate the dashboard through the shared mutation flow.
- The tenant bell reuses `/notifications/`. Its six bounded record sources are
  limited to 100 each, and the combined tenant feed is limited to 200. Overdue
  rent takes priority; remaining notices sort newest first. Repair status keys
  include visible status/schedule, so completion/rescheduling becomes unread;
  comment notices use distinct IDs and exclude internal/self-authored comments.
- Read state remains personal and workspace-scoped. Read queries filter only
  keys in the visible feed. Mark-read accepts bounded current IDs, is throttled
  and idempotent, and refetches after a stale-feed failure. Responses are private
  and no-store. Existing manager access/alerts remain available.
- Tenant Settings now exposes payment/lease/maintenance in-app preferences;
  payout preferences remain manager-only. Overdue reminders cannot be hidden by
  optional alert preferences. Portal writes invalidate notification queries.
- No new models or migrations are required. Document notices select metadata
  only, not PDF binaries/snapshots or signing secrets; repair notices never copy
  internal text, vendor contacts, costs or manager-only notes.

Validation on 2026-10-26: Django check, Ruff and migration consistency passed;
full SQLite backend suite **975 passed, 18 PostgreSQL-only skipped**. Frontend
production build and 25 existing Node checks passed. Query-count regressions cover
small versus 100-row notification/repair populations without per-row growth;
this is not a server capacity benchmark. The full suite also covers the committed
Claude messaging fixes inherited by this work; PostgreSQL concurrency cases were
not rerun locally in this task.

Synthetic browser checks passed the dashboard count/filter/reset, tenant bell,
read/unread/new-update behavior, repair navigation, error/retry/empty states,
tenant preferences and desktop/mobile/light/dark layouts. Screenshots wait for
the existing popover opening transition to finish. Evidence is ignored under
`output/playwright/mvp-*.png`; replay script `output/mvp-notifications-browser.js`.
Figma references: dashboard 259:106, tenant feed 259:112, mobile empty 259:122.

This feature is local only; no push, deployment or external send was performed.

## Test release verified — 2026-10-26

The preceding paragraph describes the implementation stage. At the user's request,
the reviewed additions and Claude's follow-up fixes are now pushed through
`3232d87` and deployed as `test-v2026.10.26.3`. Release
[CI 40370478057](https://github.com/EmmaGodfrey/dwella_suite_new/actions/runs/40370478057)
passed backend, PostgreSQL, frontend and test-deployment gates; production deploy
was skipped. Local frontend build and 25 Node checks also passed after review.

Live read-only checks verified current migrations, private message tables,
protected admin APIs, a real linked tenant's scoped feed and the manager repair
summary. The deployed UI passed the repair filter/reset and tenant notice
read/unread, linking, preference, error and mobile/dark flows with intercepted
synthetic API traffic. New outbound delivery remains disabled, production
containers are unchanged, and no message/charge/transfer was initiated by checks.

Claude's follow-up makes the combined repair row count once in Needs attention,
polls tenant notices every five minutes, clarifies channel preferences and shares
the Maintenance URL-filter helper. These were included in the reviewed release.
