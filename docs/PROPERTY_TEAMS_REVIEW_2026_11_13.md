# Property teams independent review — 13 November 2026

## Final TEST release checks — 13 November 2026

The user approved a final test run and deployment to TEST if it passed. The admin-demotion fix is committed as `b014f77`; all reviewed property-team changes are prepared for the CI-gated TEST release.

Final local checks passed: **1,743 backend tests / 36 PostgreSQL-only skips**, **50 frontend Node tests**, production frontend build, **23 deployment-policy tests**, Django system checks, Ruff and migration generation consistency. The latest full isolated PostgreSQL run passed **1,779 tests**; tagged CI independently reruns both backend database suites before allowing deployment. The separate-context browser check passed admin demotion, assignment removal and cover ending.

Before release, all 10 TEST services were running and the healthchecked services were healthy. A private baseline records TEST application counts and environment hash plus the identities of all 21 non-TEST containers for comparison after deployment. Unrelated local outreach/SMS notes are excluded. This section records pre-deployment validation; actual release status is reported by CI and the deployment handoff.

## Admin demotion fix — 13 November 2026

At the user's request, Codex fixed the remaining frontend finding locally. The scope watcher now polls for both property admins and managers, detects a role mismatch on the first fresh team response, and refreshes account access while clearing previous-scope queries. Team activity is cleared too; only the current team snapshot is preserved. A reused cached snapshot cannot trigger repeated resets before a fresh response arrives.

Changed `frontend/src/Components/Team/CoverBanner.jsx`, `frontend/src/Services/teamScope.mjs` and its Node tests. No backend authorization changes were needed. The source fix was subsequently committed as `b014f77` for the approved TEST release.

Validation: all **50 frontend Node tests passed**, including the new history/cache regression; production build passed (existing large-bundle warning). The separate-context browser reproduction now reports `liveRole=manager`, a team read after demotion, and **false** for the retained admin label, Add property and Beta property. Manager assignment removal and admin-ended cover still pass. Browser script: `output/playwright/team-role-fix-browser.js`; screenshot: `output/playwright/team-role-fix-admin-demoted.png`. Browser timers were installed before navigation so polling could be exercised deterministically. Expected 404s for revoked records occurred; no JavaScript runtime errors were observed.

The re-review finding below is retained as historical evidence and is now resolved by this change.

## Re-review of fixes through `9d0998c` — 13 November 2026

Reviewed all seven repair commits, `b98a932` through `9d0998c`. The original four backend findings are fixed. The frontend cache finding is fixed for existing managers, but one role-transition case remains. No application source was changed during this review.

### Re-review finding — Medium: an open property-admin session does not detect demotion (fixed above)

Location: `frontend/src/Components/Team/CoverBanner.jsx:20` and `:23`, with `frontend/src/Layout/Layout.jsx:28` and the default query focus behavior in `frontend/src/Services/queryClient.js:8`.

The watcher is enabled only when the **cached** account role is `manager`. An already signed-in property admin has the watcher disabled. If another admin changes that person's role to manager and assigns only Alpha Court, the existing tab never polls the team, never notices the role change and never clears its old workspace-wide queries. The account query has no interval, and its default window-focus refetch is disabled. Becoming stale alone does not schedule a refresh.

**Browser reproduction:** opened an admin's property screen with Alpha and Beta, then demoted that admin from a separate authenticated context to manager assigned only Alpha. After advancing the browser clock through two polling periods, the fresh `/accounts/me/` response said `manager`, while the open screen still showed **Property admin**, **Add property**, and Beta's address, units and rent figures. The original tab made **zero team requests** after demotion. Screenshot: `output/playwright/team-rereview-admin-demoted.png`; reproduction: `output/playwright/team-rereview-browser.js`.

Fresh backend requests enforce the new role: an independent test using the existing admin token confirms a one-property list, 404 for Beta, and 403 for receiving details after demotion. This finding concerns retained browser data and controls, not a demonstrated backend permission bypass.

**Required correction:** detect role and membership changes for both management roles, refresh account access, and cancel/clear data from the previous scope before rendering it under reduced authority. Include role-sensitive Team activity caches when dropping admin authority. Add an integration/browser regression that starts as an admin, performs the demotion elsewhere, and verifies that the old property/financial views and admin controls disappear. The present helper tests only start with a manager and cannot catch the disabled watcher.

### Fix verification

- Refused invoices leave no charge behind; post-save authorization failures roll back. The independent probe now expects the intentional 400 validation response rather than the old 403.
- Manager collection and nested receipt responses omit receiving-account and payout details, while admin responses retain them.
- Assigned managers' document detail responses now enable signing. The independent helper check supplies the lease required by the new property-specific contract.
- Covered bulk generation now records the correct covered property in `cover.change`.
- The QueryClient reset clears previous-scope records. Browser checks confirmed that remote assignment removal clears an open manager property screen, and an admin-ended cover disappears from the manager's open tab. These checks used separate authenticated contexts, a disposable local database, and accelerated browser timers.
- The private-table migration adds PostgreSQL RLS and Handy grant revocation; the PostgreSQL suite checks the four RLS flags.

### Re-review validation

- Focused team/regression suite: **36 passed / one PostgreSQL-only skip** on SQLite.
- Original independent reproductions plus credential-removal and remote-demotion checks: **eight passed**. Log: `backend/output/codex-rereview-independent.log`.
- Full SQLite suite: **1,743 passed / 36 skipped** (`APP_ENVIRONMENT=test`).
- Full isolated PostgreSQL 17 suite: **1,779 passed**. The disposable server was stopped after validation.
- Django system checks, Ruff and migration consistency checks passed against a disposable database path.
- Frontend production build passed; all **11** targeted cache/navigation Node tests passed. The existing large-bundle warning remains.
- Full backend runs and independent probes use the same fast test hasher as the initial review. PostgreSQL is isolated on loopback, with reduced write durability for test speed. No real messages, payment-provider calls, deployments or pushes were performed.

Handy/WhatsApp manager support and the invitation-mail lock follow-up remain as described in the original review; these repair commits do not implement them.

## Initial review through `e98024e` — historical findings

Reviewed `0c09428` through `e98024e` on local `develop`, against `fd997a7`.
The initial recommendation was to fix the findings below before release. See the re-review above for their current status. Application source was not changed by this review.

## Findings

### 1. High: a forbidden invoice request still creates a financial charge

Location: `backend/apps/common/viewsets.py:56`, `backend/apps/billing/serializers.py:237`, `backend/apps/audit/middleware.py:29`.

An assigned manager can POST an invoice for an accessible tenant without a lease. The serializer accepts it and `create_invoice` saves the invoice and lines. The subsequent `check_saved` rejects the invoice because it has no property, returning 403. The invoice remains saved: the independent reproduction increases the invoice count from four to five despite the forbidden response. It is then absent from the manager's property-scoped invoice list. Retrying the apparently failed submission creates further charges.

The middleware opens an explicit transaction, but only explicitly rolls back error responses for platform support sessions. DRF catches `PermissionDenied` before the exception reaches that transaction; its automatic rollback helper applies to `ATOMIC_REQUESTS`, which is not enabled here.

Reproduced on SQLite and PostgreSQL. Validate the manager's target property before saving and guarantee rollback for post-save authorization failures. Add a regression assertion for persisted invoices, lines, and notification intents after rejection. Decide how managers should issue one-off charges with an explicit property or lease.

### 2. High: receiving-account and payout privacy is bypassed through collections

Location: `backend/apps/payments/views.py:168`, `backend/apps/payments/serializers.py:142`, and nested `PaymentSerializer.online_payment` in `backend/apps/billing/serializers.py:35`.

The direct `/payments/destination/` endpoint correctly returns 403 for an assigned manager. However, `/payments/collections/` uses the unrestricted `CollectionSerializer` and returns the same receiving account inside `destination`, including its full mobile-money phone number, account name, bank name and account suffix. It also returns the nested payout details. Invoice payment/receipt responses reuse that serializer.

Reproduced with synthetic receiving details and an assigned property's collection on both databases. Restrict the collection representation for assigned managers consistently across the list and nested payment responses while keeping the permitted collection status and amount.

### 3. Medium: assigned managers cannot access the lease signing button

Location: `backend/apps/documents/serializers.py:66`, `backend/apps/documents/services.py:18`; UI gate: `frontend/src/Components/Documents/DocumentPreview.jsx:92`.

The new `active_signer` allows a manager only when supplied the lease. `DocumentSerializer.signer_is_active` still calls it without the lease and caches by user/workspace. Consequently, an assigned manager designated as landlord signer gets `can_sign=false` from the document detail API and never sees “Sign for landlord”. The new team test exercises `active_signer` directly and misses the response/UI gate.

Reproduced through GET `/documents/versions/<id>/` on both databases. Supply the document's lease, include property/lease context in the cache key, and test the full document representation. Also review the signers picker: admins currently receive only admin candidates, so they cannot select an assigned manager from the UI.

### 4. Medium: bulk billing under cover has no cover audit record

Location: `backend/apps/billing/views.py:156`, `backend/apps/common/property_scope.py:284`.

An active cover correctly lets a manager generate next month's invoices for the teammate's properties. But this collection action never records the property IDs it changed. The audit middleware therefore creates no `cover.change` event. This contradicts the Team UI promise that every covered change is recorded under the covering manager's identity and reason. Late-fee application shares the same path.

Reproduced on both databases: POST `/billing/invoices/generate/` returns 200, a covered-property invoice exists, and there are zero `cover.change` events. Record the properties actually changed by bulk operations and add an audit regression test.

### 5. Medium: ending cover retains data from the former scope in frontend caches

Location: `frontend/src/Services/team.js:30`, `frontend/src/Components/Team/CoverBanner.jsx:21`.

The comments promise to drop old data, but `invalidateQueries()` only marks it stale and refetches active queries. Inactive detail queries retain their previous data. Failed refetches also retain previous data. Document pages additionally use an infinite stale time. A local probe against the installed QueryClient confirmed that the covered property's cached data survives both invalidation and a denied refresh.

Remote assignment removal or admin-ended cover has another gap: the shell's Team query has no polling, global focus refetch is disabled, and the expiry timer follows the originally cached expiry. An already open manager tab can keep its banner and old portfolio state until another action causes a refresh. Fresh backend requests are scoped correctly; this is a browser state/revocation issue, not a demonstrated backend authorization bypass.

Cancel in-flight requests and remove/reset data for the previous scope when authority changes. Ensure manager tabs detect changed assignments, roles and cover state, and close retained record/document views. Validate with two browser sessions and an inactive cached document page.

## Additional gaps and limits

- **New private tables:** PostgreSQL inspection confirmed `relrowsecurity=false` on all four new tables: invitations, invitation-property links, assignments and cover sessions. Migration `organizations/0007_property_teams.py` omits the private-table RLS/grant-revocation pattern used elsewhere. Add that protection and a restricted-role test. No claim is made that the current Handy deployment grants access to these tables; that depends on its actual grants and allowlist.
- **Handy and WhatsApp:** assigned managers are deliberately rejected by token issuance and WhatsApp membership resolution; the added test explicitly asserts this. This avoids granting workspace-wide access, but leaves scoped assistant/chat/proof-review support unfinished relative to the requested cross-channel scope. Do not enable managers by merely adding their role to the existing allowlists. Direct SQL and existing issued-token revocation require a separate provider/RLS validation.
- **Invitation delivery:** no real email, WhatsApp message, charge, transfer or deployment was performed. Live email acceptance remains unverified.
- **Invitation locks:** team invitations call the mail transport while holding the workspace/team transaction lock. Keep this as a measured follow-up; no provider latency/load measurement was performed here.
- The existing team query-count regression passed; this review does not claim a full performance/load assessment.

## Validation and reproductions

- Claude's team tests: **28 passed** with the normal configured password hasher.
- Independent Django probes: **five failing checks** reproducing four backend findings (two checks cover signing), on SQLite and PostgreSQL. They intentionally assert the required behavior and fail on the reviewed code.
- QueryClient probe confirms retained data after invalidation and a failed refresh.
- Django system checks, Ruff and migration generation checks passed using a disposable SQLite path. An initial check against the configured application database warned that its file could not be opened; that database's applied history was not validated.
- Frontend production build passed, with the existing large-bundle warning; all eight navigation-state tests passed. No new browser walkthrough was performed.
- Full SQLite suite in the test environment: **1,735 passed / 35 skipped**.
- Existing API tokens and browser sessions both stopped seeing properties immediately after assignment removal, and lost portfolio access after membership deactivation: **two additional independent checks passed**.
- Full isolated PostgreSQL 17 suite: **1,770 passed**. The temporary server was stopped after validation.
- Full suites and independent probes use an MD5 test password hasher for speed; the focused 28-test run used the normal configured hasher. The disposable PostgreSQL instance uses reduced write durability to accelerate test transactions; this run does not validate crash durability.

Private, ignored reproduction artifacts:

- `backend/output/test_codex_property_team_review.py`
- `backend/output/codex-independent-review.log`
- `backend/output/codex-team-pg-repros.log`
- `frontend/output/codex-team-cache-review.mjs`
- `backend/output/codex-team-postgres/suite.log`
- `backend/output/codex-team-sqlite-testenv.log`

The first full SQLite run inherited the local production environment and had six existing platform/MFA test failures plus four independent probe failures (1,729 passed / 35 skipped). All existing tests passed when the suite was repeated with the intended test environment; those six initial failures are not attributed to this feature.
