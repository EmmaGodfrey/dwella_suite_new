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

## Status

In progress. No performance or production-readiness claim is made from the
previous payment functional test counts.
