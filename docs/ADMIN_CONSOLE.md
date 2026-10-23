# Admin console

## Phase 1: support access foundation

The backend supports explicit, audited access to one landlord workspace. The admin
console and acting mode are implemented following the approved Figma review.
Apply the audit migration before using these endpoints.

Staff and superusers can start support sessions. A superuser-only permission is
available for the later user and workspace management endpoints. Signing in as an
admin does not grant access to individual landlord data by itself: portfolio endpoints
return 400, `Choose a workspace first.` The existing dashboard endpoint is a compatibility
exception: it returns aggregate platform figures without individual property/unit records.

1. `POST /api/v1/platform/support-sessions/` with `organization` (workspace public
   UUID) and `reason` (5–300 characters after trimming). Starts are limited to ten
   per hour per administrator. Suspended workspaces cannot be opened.
2. Send `X-Dwella-Workspace: <workspace UUID>` on subsequent API calls. The resolver
   accepts it only for the authenticated admin's unended session whose expiry is
   still in the future. Sessions last four hours. The most recently started valid
   session for that admin and workspace supplies the reason. A malformed, unknown,
   expired or ended context returns 403 on workspace-scoped endpoints in the standard
   response envelope. Account and platform lifecycle requests remain usable; `/me/`
   reports a null acting workspace when the header is invalid.
3. `/api/v1/accounts/me/` includes `access.acting_workspace` with the workspace
   `id`, `name`, `session_id`, `reason`, and `expires_at`. It is null without a
   selected workspace. Capabilities reflect owner access only while acting.
4. `GET /api/v1/platform/support-sessions/?active=true` lists the caller's live
   sessions with standard pagination. Omit the filter for history or use
   `active=false` for ended or expired sessions. Other admins' sessions are private.
5. `POST /api/v1/platform/support-sessions/<session UUID>/end/` ends the caller's
   session. Stale workspace headers do not block starting, listing or ending sessions.
6. `POST /api/v1/accounts/logout/` ends all the caller's support sessions, revokes
   their API token and ends their Django session. Frontend logout calls
   this endpoint before clearing local credentials. Merely deleting a browser token
   does not notify the server; the four-hour expiry remains the backstop.

The admin keeps their own identity throughout. Viewsets, object permissions,
dashboard, reports and CSV, notifications, onboarding, organization settings and
Smart Invoice settings resolve the same organization. A valid session for one
workspace never grants access to another workspace's records or relationships.
Non-admin workspace headers are ignored, and their existing membership and role
rules determine access. Existing session authentication CSRF checks remain intact.
Admins cannot create or delete organizations through the landlord organization
endpoint; those actions require the guarded platform endpoints in a later phase.

Starting and ending sessions records an audit event. Every successful unsafe API
request under a resolved support session records the admin, organization, action,
resource type and ID, request ID, session ID and reason. Custom API views use the
view name and workspace ID when no single model resource exists. Request payloads
and credentials are never copied into the audit metadata. Failed requests do not
record a successful write; support writes and their audit entries share a database
transaction, so audit failure rolls back the business change. Only workspace writes
lock and revalidate the support-session row, serializing against leaving. Reads use
an unlocked validity check. The request middleware does not open transactions for
reads or unrelated account/platform/marketing actions; lifecycle views keep their
own atomic transactions. Joined organization rows are not locked by the resolver.
Audit events and support-session records are view-only in Django admin, including
for superusers; all session lifecycle changes go through the audited API.

Later phases add platform users, workspaces, audit browsing and platform dashboard
APIs. Suspending workspaces and landlord consent settings are outside Phase 1;
the console plan defines their remaining decisions. Nothing here enables deployment.

## Review notes (Claude, 22 October 2026)

Phase 1 was reviewed at `1d418e9`. The full backend suite and Ruff pass. Fix these before
Phase 4, or before any merge of develop into main:

1. **Release blocker: the admin Dashboard breaks.** `GET /api/v1/properties/dashboard/`
   now returns 400 "Choose a workspace first" for a platform admin with no support
   session. The live frontend still calls it for the admin "Administration" page. Do not
   merge develop into main until Phase 4/6 ships a platform dashboard endpoint and
   screen. Alternatively, keep a platform summary branch in that view.
2. **A stale workspace header locks the admin out.** If `X-Dwella-Workspace` names an
   expired or ended session, `WorkspaceAuthenticationMixin` raises 403 on *every* request,
   including `/accounts/me/`, `/accounts/logout/` and `POST /platform/support-sessions/`.
   The admin can't sign out or start a new session until the frontend drops the header.
   Recommended fix: record the invalid header during authentication and raise only from
   `resolve_workspace(required=True)` on workspace-scoped endpoints. Ignore the header on
   `/accounts/*` and `/platform/*`. Add tests for all three requests.
3. **Lock scope.** The audit middleware now wraps every request in `transaction.atomic`,
   and every admin request takes `SELECT … FOR UPDATE` on its support-session row until
   the response is sent. On Postgres, the frontend's parallel queries for one admin will
   queue behind each other. Any SMTP send inside an admin request (beta sign-in
   details) also holds the transaction open. Consider taking the lock only for unsafe
   methods. GETs can re-check `ended_at`/`expires_at` without locking.
4. **SQLite hides lock behaviour.** The test suite runs on SQLite, which ignores
   `select_for_update`. Run the support-session tests against Postgres (as in CI or
   compose) before release.

## Review resolution (Codex, 22 October 2026)

All four findings above have been addressed without frontend changes:

1. The existing dashboard URL retains a platform-summary branch for staff and
   superusers without a selected workspace, preserving the shipped response shape.
   It exposes aggregates, with empty recent-properties/top-units/town lists. A supplied
   invalid workspace cannot fall back to that branch; selected workspaces stay scoped.
   Portfolio lists and writes still require reasoned support access.
2. Optional context resolution records invalid context and raises only when workspace
   access is required. Account/platform operations ignore the header, except `/me/`
   which reports a valid optional context or null. Real-token tests cover recovery
   from expired, ended, unknown, malformed and blank headers, plus unauthenticated
   and non-staff denial. Logout still ends sessions and revokes credentials.
3. Reads never request a support-session row lock. Workspace writes upgrade the
   optional authentication read to a locked validity check inside the audited-write
   transaction, using `FOR UPDATE OF` only the session row. This prevents a write
   from using access that ended while it waited. Unrelated platform work, including
   beta email delivery, does not hold that session lock or the middleware transaction.
4. `apps/audit/test_support_concurrency.py` exercises real competing Postgres
   connections. A read succeeds while another request holds the session lock; a
   waiting write fails if that session ends before it obtains the lock. The new
   `backend-postgres` CI job runs the audit suite on Postgres 16 and gates deployment.

Validation: 317 passed and 2 Postgres-only tests skipped in the full SQLite suite;
all 75 audit/support tests passed on isolated Postgres 16, including both lock tests.
Ruff, Django check, migration consistency and fresh Postgres migrations passed.
The two lock tests deliberately skip on SQLite and must remain enabled on Postgres.
The GitHub workflow was parsed locally; its new job will run when a PR/push triggers CI.
Nothing was pushed, merged into main or deployed. Frontend implementation remains paused.

## Completed console (23 October 2026)

The Platform sidebar provides Administration, Workspaces, Users, Identity checks,
Beta signups and Audit log. Staff can manage ordinary users and memberships, review
identity submissions, suspend/reactivate workspaces and transfer ownership. Granting
platform admin rights and permanent deletion require a superuser. Self-protection,
last-owner/last-superuser checks and typed deletion confirmations remain authoritative
on the backend. Suspension blocks portfolio reads and writes and ends support access.

Open a workspace from its detail screen or the sidebar picker, supply a 5–300 character
reason, and use the normal landlord screens with owner access. The support banner
shows workspace, reason, time remaining and Leave. Switching, leaving, expiry and logout
abort old requests and clear the query cache. In-flight mutations prevent switching or
logout. Platform pages remain available while acting: /dashboard shows platform
Administration; /workspace/dashboard shows the selected landlord's dashboard.

GET /api/v1/platform/dashboard/ returns aggregate workspace/user counts, beta statuses,
open support sessions, pending identity checks and collections for the current Lusaka
business month through today, excluding reversed payments. No individual financial
records are returned. Workspace detail includes a paginated properties summary via
GET /api/v1/platform/workspaces/{id}/properties/; private portfolio operations still
require support access.

Audit log supports actor, workspace, action, resource, date and support-session filters,
a detail drawer and CSV export. User/workspace detail shows the latest five relevant
events. CSV cells escape spreadsheet formulas and exports use private/no-store headers.
Account sign-in/2FA changes and important landlord financial/lease actions are audited
outside support mode too; support writes keep their reason and original actor.

Validation on 23 October: full SQLite suite 411 passed / 2 Postgres-only skips; full
isolated PostgreSQL 17 suite 413 passed, including competing-connection regressions.
Django check, Ruff, migration consistency, support-context unit checks and production
frontend build passed. Browser review covered audit filtering/export, workspace details,
acting navigation, leave, light/dark, narrow screens and viewport reflow corresponding
to 67%/200% zoom. Preview data/artifacts remain ignored; no deployment was performed.
