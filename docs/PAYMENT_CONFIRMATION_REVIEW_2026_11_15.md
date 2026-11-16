# Payment confirmation review — 15 November 2026

Scope: Claude's commits `8bc04e1` and `e9dca40`, tagged `test-v2026.11.15.4`, and follow-up `55eee2b`, tagged `test-v2026.11.15.5`. Review only; payment implementation remains with Claude. No additional payment, refund, withdrawal, provider request, deployment or application change was performed by this review.

## Follow-up fix review — 55eee2b

### Final release and separately authorized live comparison

**Second user-operated browser run (INV-0013/RCT-0013), explicitly requested as one more K1 test:** succeeded/settled, balance zero, no payout. Request19:25:41.456498UTC; provider completion19:26:02.843; first webhook19:26:10.758902; receipt19:26:11.139894. Request-to-completion **21.387 s**, completion-to-webhook **7.916 s**, webhook-to-receipt **0.381 s**; total **29.683 s** versus **40.165 s** in the previous browser run. Application-side verification remained essentially unchanged at0.38s. The variation is before the first recorded webhook; these timestamps alone do not separate PIN approval, operator/provider processing, delivery and ingress delays. Exact device PIN time and browser success-render time were not captured. Evidence `output/repeat-browser-payment-20261115.log`; user initiated the normal checkout, observer only read evidence and exited after success.

**Subsequent user-operated browser run (INV-0012/RCT-0012):** payment request created19:13:26.911353UTC; Lenco reported completion19:14:06.518; first webhook06.695562; receipt07.076758. Total request-to-receipt **40.165 s**: **39.607 s** before provider completion (including phone authorization, exact PIN time unavailable), then **0.559 s** completion-to-receipt (**0.381 s** webhook-to-receipt). User reported the visible wait exceeded ten seconds, consistent with these records. The earlier sub-second figures describe final confirmation, not the full payment flow. Browser's exact visible-success time was not captured. This run used the normal tenant browser flow after explicit temporary TEST collection activation; no maintenance script initiated its payment. Evidence `output/browser-invoice-timing-20261115.txt`. Successful, settled K1, balance zero, no provider requests or mutations during the timing inspection.

`efd85db` corrected only the regression test: it stubs connection cleanup inside that rollback-based test and fails on unexpected worker exception logging. Production cleanup is unchanged. TEST release `test-v2026.11.15.6` passed all gates and deployment in [run 43748750842](https://github.com/EmmaGodfrey/dwella_suite_new/actions/runs/43748750842). Six runtime source hashes matched in both backend and worker; healthy backend, fresh worker heartbeat and shared Redis verified.

The user separately authorized a second K1 Airtel test after deployment. It succeeded and settled: **INV-0011 paid, RCT-0011, zero outstanding**, provider fee K0.01, no payout. The existing checkout API view ran in an isolated maintenance process; shared alpha/payment/payout settings stayed unchanged. This operational experiment is separate from the read-only code review.

| Stage | Before (one sample) | After `.6` (one sample) |
| --- | ---: | ---: |
| Provider completion to first webhook evidence | 1.947 s | 0.288 s |
| First webhook evidence to receipt creation | 4.589 s | 0.331 s |
| Provider completion to receipt creation | 6.536 s | 0.619 s |

Application-side webhook-to-receipt delay fell by about **93% in this comparison**. The completion-to-receipt improvement also includes faster Lenco webhook delivery; do not attribute all of it to the worker fix. One sample per version is not a latency distribution/load benchmark. Browser display timing was not measured.

Post-change UTC: request18:59:10.686751, initial response18:59:13.044967; provider initiated18:59:11.007/completed18:59:34.756; first webhook18:59:35.043623; receipt18:59:35.374517. User's “PIN submitted” message sampled around18:59:30 is an approximate message marker, not device telemetry. Evidence: `output/postfix-k1-test-20261115-result.txt`, `output/postfix-k1-watch-20261115.log`, `output/payment-confirmation-before-after-20261115.json`. Observer finished on success. Both paid test invoices/receipts are retained as evidence; no further charge, refund or payout authorized.

**The original runtime P2 is resolved in local checks, but PostgreSQL CI subsequently found a blocking regression-test setup issue. Release `.5` did not deploy.**

### PostgreSQL CI failure found while waiting for the second payment test

Both branch run `43747931549` and tagged run `43747935730` failed `test_worker_runs_a_three_second_recheck_without_waiting_out_its_pause` at `apps/payments/test_fast_confirmation.py:156`. Captured logs show `psycopg.OperationalError: the connection is closed` while `idle_seconds()` tries to query the next deadline. The worker catches the query error and falls back to five seconds, so the timing assertion fails. Deployment was skipped.

The module uses ordinary `pytest.mark.django_db` rollback transactions. Calling the real worker's `close_old_connections()` inside that test can close the PostgreSQL connection enclosing the fixture transaction. SQLite's in-memory connection handling did not expose this in local validation. The regression should use a transactional database test (for example, mark this worker-loop test `django_db(transaction=True)`) so fixture writes are committed and the real connection lifecycle can reconnect, or explicitly isolate connection cleanup if that is outside the test's scope. Prefer the transactional variant when exercising the actual worker lifecycle. Re-run this case on PostgreSQL and the normal release gates; do not bypass the failed gate or weaken runtime cleanup.

This is a CI/test-lifecycle diagnosis, not evidence of a live tenant payment failure. Logs: `output/postfix-tag-ci-failure.log`, `output/postfix-branch-ci-failure.log`. The user authorized one additional K1 test after successful deployment, but no second invoice/collection or prompt has been created. The prepared run remains pending; payment implementation/test correction stays with Claude under the existing ownership instruction.

The worker now reads the earliest scheduled collection check before waiting and limits the pause to that deadline, with a 0.25-second minimum and the original five-second maximum. A new webhook can still interrupt the wait. The query selects one timestamp, filters by the active provider environment, and uses the existing partial next-check index; no rows are loaded to compute a Python minimum. Query failure falls back to the original idle interval.

Independent reproduction using the real worker loop, real `idle_seconds()` query and a synthetic database row due three seconds ahead: **3.000 seconds**, compared with **5.016 seconds** before the fix. Additional checks confirmed the lookup issues one SQL query, ignores another environment's overdue row, retains the maximum pause for distant work, and applies the 0.25-second floor for overdue work. Evidence: `output/test_payment_fix_review.py` (two independent tests passed).

Full payment regression suite: **213 passed, 8 PostgreSQL-only tests skipped locally**. Django system check and payment-module Ruff checks passed. The two new committed regression tests also passed within that suite. This backend-only fix did not change the frontend or financial verification/submission logic.

At the initial follow-up review checkpoint, `.4` had completed CI/deployment and was live on TEST; the backend was healthy and the worker heartbeat fresh. `.5` was pushed but not deployed. Its PostgreSQL CI gate subsequently failed as described above, and deployment was skipped. No post-change handset-to-screen latency measurement has been performed. Shared alpha/payment/payout flags remain unchanged.

## Original finding — resolved by 55eee2b

**P2 — The worker's idle wait can miss the new three-second retry deadline.**

`backend/apps/payments/schedule.py:54` schedules a pending/failed/expired collection for three seconds after a recent webhook when the provider's authoritative status has not caught up. After checking that row, `run_payments_worker.py:64` immediately starts another cycle. Since the row is not due yet, that cycle returns no work and line 67 waits for the fixed five-second idle period. The original webhook nudge has already been consumed. Without another event, nothing wakes the worker at the three-second deadline.

I exercised the actual `Command.handle()` and `wake.wait()` with an isolated in-memory cache and synthetic work scheduled three seconds ahead. The next worker cycle happened after **5.016 seconds**, rather than three. This reproduction made no database or provider calls. Evidence: `output/check_confirmation_retry_wait.py` and `output/payment-retry-wait-review.json`.

This affects the follow-up path when a valid webhook arrives before Lenco's status endpoint reflects the result. It does not create a false payment or duplicate debit. The existing new unit tests check `next_check_at` but do not exercise the worker waiting until that deadline. The worker wait needs to respect the nearest due work, with a worker-loop regression check. Do not solve it by multiplying every provider poll.

## Positive checks and limits

- Signed webhooks and authorized tenant status requests nudge the worker only after the database transaction commits. The nudge carries no payment data and does not authorize an action.
- Receipts still depend on the existing authoritative provider verification, ledger and idempotency rules. The diff does not change the collection amount, debit submission or receipt creation logic.
- The frontend's two-second refresh reads saved Dwella records. It backs off after three and ten minutes and stops when no pending payment remains. It is used by the tenant invoice checkout.
- The wake mechanism requires a shared cache. TEST backend and payment worker both use Django RedisCache, verified on the live containers. A nudge cannot interrupt a worker already doing provider I/O or balance reconciliation; no hard end-to-end latency guarantee has been established.
- The last real K1 timing run preceded these commits. Its observed times must not be presented as post-change measurements. A new real-money run requires separate explicit authorization.

## Validation and deployment status

- Focused backend wake/schedule tests: **21 passed**.
- Frontend checkout/feedback tests: **11 passed**.
- Django system check and payment-module Ruff checks passed.
- Local Vite emitted the production build and its existing large-chunk warning. The PowerShell redirection wrapper returned a failure status on stderr; the independent GitHub frontend build gate is successful.
- Full local payment regression run: **211 passed, 8 skipped** (PostgreSQL-only cases); this does not substitute for the full PostgreSQL CI gate.
- At 18:28 UTC, live TEST backend and worker still ran the previous code (`wake.py` absent; source hashes differ). The tagged release was pushed but its deployment was not complete. Backend, frontend and runtime-policy CI gates passed; PostgreSQL was still running. This checkpoint does not establish the final release status.

Release evidence: [tagged CI run](https://github.com/EmmaGodfrey/dwella_suite_new/actions/runs/43746658605). Runtime checks: `output/review_payment_confirmation_release.py`, `output/payment-confirmation-release-review.json`. No shared payment/alpha/payout flags were changed.
