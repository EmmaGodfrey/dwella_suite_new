# Backend efficiency audit

Started 2026-10-25. Baseline: local develop at 148b3b1; payment changes are being
made concurrently by Claude. This audit covers every other backend app and
shared request/storage/worker infrastructure. Payments, billing/payment service
semantics and scheduler changes are reserved for Claude; related findings are
reported for handover, not edited here. No live financial requests or load tests
will be used. Test data and databases are isolated from development/production.

## Method

1. Inventory all installed apps and routes, serializers, ORM summaries, bulk jobs,
   document/storage work, indexes and shared authentication/workspace paths.
2. Measure representative request query counts at small/full page sizes, and bulk
   work at small/larger batches. Inspect SQL and PostgreSQL plans where useful.
   Separate observed costs from risks inferred from source inspection.
3. Fix confirmed, bounded non-payment issues in focused commits, retaining tenant
   isolation and response contracts. Add scaling/query regression tests.
4. Run Django checks, Ruff, migration consistency and relevant tests during fixes;
   run the full backend suite for final shared behavior. Report remaining risks
   with exact code locations, priorities and owners.

## Findings and changes

The broad source review found avoidable per-row queries, full-history work and
external work inside transactions. The first fixes remove measured per-row
queries without introducing dependencies, cross-request permission caches or
changes to money arithmetic. Remaining findings below are actionable work, not
claims that those areas have already been optimised.

### Measured list queries

Synthetic authenticated requests, cold application cache each time, SQLite,
`page_size=1` versus `25`. Counts include permission checks and pagination.
Twenty-five actual rows are returned by each nonempty list in the regression
fixture; properties/workspaces have additional rows. The original properties
and workspace baselines contained only one row, and the audit-event baseline
was empty; those baselines must not be read as scaling evidence.

| Endpoint | Before: 1 / 25 | After: 1 / 25 | Change |
| --- | ---: | ---: | --- |
| Properties/units | 5 / 29 | 4 / 4 | Join the workspace already used by the serializer |
| Tenants | 7 / 31 | 6 / 6 | Same workspace join |
| Leases | 6 / 30 | 5 / 5 | Same workspace join |
| Maintenance requests | 5 / 29 | 4 / 4 | Same workspace join |
| Document versions | 7 / 55 | 6 / 6 | Reuse prefetched signatures and request-local signer check |
| Platform users | 8 / 80 | 5 / 5 | Render access from joined state and prefetched memberships |
| Outreach contacts | 4 / 28 | 3 / 3 | SQL `Exists` suppression annotation on read actions |
| Tenant leases | 7 / 7 | 7 / 7 | Already bounded in this fixture |
| Tenant invoices | 8 / 8 | 8 / 8 | Already bounded in this fixture |
| Tenant maintenance | 7 / 7 | 7 / 7 | Already bounded in this fixture |
| Document originals | 4 / 4 | 4 / 4 | Already deferred in manager metadata lists |
| Properties | Not comparable | 4 / 4 | Populated post-change fixture |
| Platform workspaces | Not comparable | 4 / 4 | Populated post-change fixture |
| Platform audit events | Not comparable | 3 / 3 | Populated post-change fixture |

Tests use DRF force authentication to isolate request/permission/serialization
work; login/token verification costs are not included. Query count is only one cost dimension: constant
queries can still read excessive rows, bytes or history.

Tenant document metadata now excludes PDF originals, unsigned PDFs, signature
images and signed PDF copies from SELECTs. A regression test verifies selected
columns and the actual private download bytes. Metadata still returns the same
fields; the file endpoint explicitly loads the requested PDF.

Claude separately committed bulk portfolio-import lookups in `ba9e54c`. This
audit reuses that implementation rather than maintaining a competing change.
An additional 500-row tenant test checks a single duplicate-lookup query,
workspace isolation, archived duplicates and a fresh lookup after preview.
Unit imports currently load all unit names for the submitted properties; query
batching is fixed, but the lookup working set can still grow with those properties.

### Prioritised remaining work

**P1 — reports scale with the complete portfolio even for one displayed row.**
`backend/apps/reports/views.py`, `PortfolioReportView.get`, `rent_roll`,
`arrears`: both report builders materialise every row and related records before
Python pagination. CSV then builds a second full text buffer. Move totals and
age buckets to SQL, slice the main queryset before loading relations and stream
exports in batches. Preserve Decimal output, aging boundaries, property scope
and CSV formula escaping. Validate equal totals on empty, partial-payment,
void/paid, vacancy and multi-property datasets before shipping. Source-confirmed;
large-portfolio latency/RSS has not been measured.

**P1 — shared reference allocation grows while holding the workspace lock.**
`backend/apps/common/references.py`, `next_reference`: loads all historical
reference strings and finds the maximum in Python under an organization row
lock. Lease/invoice/receipt/maintenance creation can queue behind one another.
Use a transactional per-workspace/per-kind counter with unique constraints and
a migration that preserves existing references. Do not remove the lock or use
`count()+1`. Coordinate this with Claude because billing calls this helper.

**P1 — ZRA submission performs external work under a row lock.**
`backend/apps/integrations/smart_invoice.py`, `submit_receipt`, calls `save_sales`
inside `atomic()` after `select_for_update()`. `queue_sale_receipt` and
`queue_refund_receipt` use `on_commit`, which still executes in the request
worker; it does not create a background job. Device initialization also makes
multiple client calls inside `SmartInvoiceInitialiseView.post`'s transaction.
The shipped client is a fake, so current network latency is not measured.
Before enabling a real client, use a persisted, bounded worker with short claims,
timeouts and provider-aware idempotency/ambiguous-result handling. A blind retry
of fiscal submission is not an acceptable performance fix.

**P2 — outreach list/import work remains proportional to recipients.**
`backend/apps/outreach/serializers.py`, `EnrollmentSerializer.get_review`, calls
`review_snapshot` per pending row; it checks suppression, loads settings and
sequence steps and renders every message. `csv_import.py` repeats serializer
duplicate checks, explicit duplicate checks and suppression checks per row (up
to three reads for each new valid contact). Confirm also loops validation and
audited writes under the settings lock. Batch read lookups for the submitted
emails; retain authoritative send-time suppression checks. Prefetch review
inputs or expose detailed previews only on explicit review. Never send mail as
part of an audit/benchmark.

**P2 — nested histories are not bounded by top-level pagination.**
`backend/apps/tenants/views.py` prefetches all lease and invitation history for
each displayed tenant. `audit/workspace_views.py` returns every membership per
workspace. Portal invoice and maintenance details include their full histories.
These do not produce the measured N+1 pattern but grow in bytes and Python work.
Portal overview also returns all current leases and awaiting-signature documents
for the linked tenancy records.
Use filtered `Prefetch(..., to_attr=...)` for display-only current records;
separately paginate history/member views. Do not filter the canonical relation
cache used by deletion/history checks, or silently omit contractual API fields.

**P2 — some email requests hold workers and locks through SMTP.**
`backend/apps/accounts/invitations.py`, `issue_tenant_invitation`, sends account
mail inside an atomic section after locking the tenant. Marketing welcome
delivery uses `on_commit`, still synchronously. `EMAIL_TIMEOUT` defaults to 20
seconds. Extend durable outbox delivery to those paths while preserving existing
success/failure semantics and duplicate protection. Document signing already
has a durable claim/send/finish outbox in `documents/outbox.py`; reuse its
principles rather than adding a second queue dependency without need.

**P2 — PDF generation and retention add CPU, lock time and database bytes.**
`backend/apps/documents/services.py` generates invoice and lease PDFs inside
atomic work. Invoice generation locks an invoice while rendering. Current and
unsigned PDF copies plus signature evidence remain binary database columns.
Metadata deferral fixes reads, not retention/database backup growth. Consider
rendering outside short transactions followed by a fingerprint/version recheck,
and private immutable object-storage references with audited retention. Preserve
signature evidence and do not delete old agreements as an optimisation.

**P2 — media backup has an object-count ceiling despite streaming file bytes.**
`backend/apps/scheduler/media_backups.py` streams object bytes and reads restores
in 1 MiB chunks, but accumulates a full manifest and tar member list in memory;
verification rejects manifests above 8 MiB. Large numbers of small objects can
eventually prevent a valid backup. Partition archives/manifests and exercise a
many-small-object restore before approaching that limit. Scheduler code is
reserved for Claude; this audit makes no changes there.

**P3 — measure database plans, search and deployment costs before tuning.**
Default pagination is bounded (50, maximum 200); notifications cap each of six
sources at 100; dashboard sample lists cap at five; audit CSV caps at 10,000.
Keep these bounds. Broad `icontains` searches, deep OFFSET pages, aggregate
counts and correlated workspace summaries still need realistic PostgreSQL plans.
Foreign-key/unique indexes already cover many point lookups. Case-insensitive
suppression/search expressions and organization/status/date list filters are
index candidates, not justification for speculative migrations. Measure query
time, rows/buffers, lock waits, CPU, peak RSS and p95 under representative data
and concurrency first. Verify shared Redis/throttle configuration and worker/
connection budgets against the deployed process count, without weakening auth.

### App coverage

All 23 app packages were inventoried. Coverage below distinguishes source review
from synthetic request measurements; it is not a claim that every endpoint was
load-tested.

| App | Review and outcome |
| --- | --- |
| accounts | Access-state projection extracted without changing fresh authorization reads; invitations/SMTP risk above; existing auth tests retained |
| assistant | JWT workspace lookup and transactional action idempotency reviewed; underlying creation/reference costs inherited; no auth caching added |
| audit | Users measured/fixed; populated event/workspace lists measured; member growth and bounded CSV export reviewed |
| billing | Read-only boundary review; transactional payment/reference/fiscal effects handed over; Claude owns changes |
| common | Workspace serializer join fixed; permission projection shared without changing decision inputs; pagination/cache/storage/reference paths reviewed |
| documents | Manager metadata/signing query growth fixed; portal binary reads fixed; rendering/outbox/storage growth reviewed |
| imports | Reused Claude's batch fix; added independent 500-row scope/freshness regression |
| inspections | URL/app scaffold, no implemented workload to benchmark |
| integrations | Fiscal receipt queue/submission/device initialization reviewed; external work/lock risk above |
| leases | List measured/fixed through common join; lifecycle/reference dependencies reviewed without changing transitions |
| maintenance | List measured/fixed; detail prefetch, photo limits and summary aggregates reviewed; existing unordered-pagination warning remains |
| marketing | Application/email sequence paths reviewed; durable sending versus synchronous welcome discussed above |
| notifications | Six source limits and joined relations reviewed; predictable bounded work, no global cache of money totals |
| organizations | Workspace and membership access reviewed; membership endpoint joins organization/user; no new cache |
| outreach | Contact list measured/fixed; review/import/send-time suppression paths reviewed; remaining batch work above |
| owners | URL/app scaffold, no implemented workload to benchmark |
| payments | Excluded from edits; Claude owns ongoing reconciliation/worker/expiry/idempotency fixes |
| portal | Lease/invoice/maintenance lists measured; document metadata/file delivery validated; nested history/overview growth noted |
| properties | Property/unit lists measured; dashboard SQL aggregates and five-row samples reviewed |
| reports | Full materialization and export buffering confirmed by source; prioritised before larger portfolios |
| scheduler | Read-only worker/backup boundary review; payment-worker changes owned by Claude; manifest limit noted |
| subscriptions | Policy/resource counts and workspace capacity lock reviewed; retain lock for concurrent capacity correctness |
| tenants | List measured/fixed; prefetch history growth, archive protection and import isolation reviewed |

## Reproduction and validation

Run from `backend/` with the project environment:

```powershell
python -m pytest apps/common/test_backend_efficiency.py -s
python -m pytest apps/imports/test_batch_efficiency.py
python manage.py check
ruff check .
python manage.py makemigrations --check --dry-run
python -m pytest
```

The scaling test writes synthetic SQL/query measurements to the checkout's
ignored `output/audit-query-measurements.json`. No provider calls or customer
data are required. The signing fixture uses current fingerprints and actual
signing status; stale terms would otherwise bypass the expensive branch and
produce a misleading result. Tests check revocation, suspended workspaces,
changed email, unverified access, signatures, current suppression and private
file delivery alongside query scaling.

The runtime does not expose in-place model switching. The access projection
change follows plan → implement → validate with fresh canonical permission
checks kept intact and comparison tests for every persona.

Final validation on 2026-10-25:

- Full PostgreSQL backend suite: **828 passed** in 351.46 seconds, using the
  separate local `backend_efficiency_audit` database and no live credentials.
- Django system check: no issues. Ruff: all checks passed. Migration consistency:
  no changes detected. Git whitespace check passed.
- Corrected SQLite query/access/import probes: **21 passed**. The earlier broad
  SQLite run had 788 passing tests, 15 skips and one failure in the newly written
  test's use of `.content` on a streaming file response. The test now reads
  `streaming_content`; private download bytes pass in the final PostgreSQL suite.
- Existing warnings include Django/DRF deprecations, the isolated checkout's
  absent collected static files and maintenance pagination without a default
  ordering. Stable maintenance ordering remains a follow-up; these warnings
  have not been silently suppressed.

The validated combined snapshot is audit branch `fa72a68`: Claude's committed
work through `a00be21` plus this audit's fixes and import regression test. The
five non-payment implementation/test commits were integrated into local develop
through `55b814a`. Claude's subsequent payment-only changes remain his validation
scope; this audit does not certify an actively changing payment implementation.
No production timing, financial readiness or deployment claim is made from
functional test counts. Nothing was pushed, deployed or financially enabled.
