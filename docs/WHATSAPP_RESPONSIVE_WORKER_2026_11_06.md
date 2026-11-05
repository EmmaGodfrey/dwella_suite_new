# Responsive WhatsApp worker

The handset pilot showed 29.91–46.36 seconds from webhook receipt to reply creation
(five messages, median 40.77 seconds). Reply claim took 0.02–0.04 seconds. The
minute scheduler, whose observed interval was 60.04–62.37 seconds, dominated delay.
These are queue timings, not a measurement of handset network latency.

## Delivery path

The existing signed webhook commits a deduplicated PostgreSQL inbox row, then
best-effort signals a bounded Redis list. The list contains only a constant wake
hint, never message content, phone numbers or credentials. Atomic trimming limits
each of three lane keys to one item; idle keys expire after 60 seconds. Wake I/O
has a 200ms socket/connect timeout. A Redis error does not reject a committed
webhook or become the authority for permissions or money.

`python manage.py run_whatsapp_worker` runs three fixed threads:

- **fast** processes one eligible inbox turn, then sends one ordinary reply;
- **files** fetches one draft attachment and sends one PDF/evidence reply;
- **notices** dispatches one payment-proof review notice.

Each thread blocks on its own Redis list for up to two seconds when idle, then
rechecks durable database work. A missed wakeup, Redis restart or outbox write
without a wake hint therefore recovers without webhook replay. Database failures
back off. Idle polling is bounded, and there are no per-pass JobRun rows.

One PostgreSQL session advisory lock per lane prevents a second command instance
from becoming another consumer, including during Redis outages. Lease connections
are separate from the short-lived work connections and released on exit. SQLite
development supports a single process only. There are up to six database
connections per active worker process: three leases and three processing threads.

The responsive inbox query admits the oldest queued event per phone, respects
retry availability, and waits for that phone's queued/sending reply before
advancing another turn. Other phones remain eligible. The admission uses bounded
queries, rather than a per-row lookup. Existing binding, workspace, STOP, consent,
claim, correlation and uncertain-send protections still apply. Slow file work
does not share the fast thread. An upstream provider timeout can still delay that
lane; the service does not promise a particular handset delivery time.

## Activation and rollback

The Compose service `whatsapp-worker` uses the existing backend image, dropped
capabilities, bounded logs, a 384MiB memory limit, and a 90-second shutdown grace.
No new dependency, database table or migration is required.

`APP_WHATSAPP_WORKER_ENABLED` defaults to **false**. With it false, the existing
minute `run_whatsapp` job retains its previous behavior. With it true, that job
performs retention cleanup only; the dedicated service owns processing. Keep the
`whatsapp` scheduler entry for cleanup. All existing self-service, runtime,
transport and allowlist controls remain applicable.

For an authorised test release, deploy first, then enable the flag in the protected
test environment and recreate backend, scheduler and the new worker. They must
agree on the flag and Redis URL. The Compose services use their environment's
existing Redis cache database. Check all three heartbeat entries in scheduler
status. Stop the dedicated worker before disabling the flag across services to
restore the minute scheduler. Do not use this switch to bypass held/uncertain
sends or consent.

Production activation remains a separate release decision. Measure real handset
queue and provider timings after activation; 1–3 seconds for ordinary replies is
a target, not an established outcome.

## Validation

The dedicated regression suite covers committed/rolled-back/duplicate webhook
wakeups, Redis failure and batched-outage backoff, recovery without a hint,
per-phone ordering, retry isolation, bounded admission query count, file isolation,
authority/STOP changes, uncertain sends, scheduler handover and PostgreSQL session
lease exclusion/release. The final focused SQLite run passed 22 cases with the
PostgreSQL-only lease case skipped. Release CI runs the full SQLite/PostgreSQL
backend suites, frontend build and resolved-container runtime policy before test
deployment.

Running the final wake module against isolated keys in existing test Redis gave
20 wake samples: median **0.50ms**, minimum **0.31ms**, maximum **1.75ms**. One hint
remained after 100 notifications, with a 60-second expiry. No customer messages
were created or sent by this measurement. This measures Redis signalling, not the
complete webhook-to-handset path.
