# Admin console

## Phase 1: support access foundation

The backend supports explicit, audited access to one landlord workspace. The admin
console screens are awaiting Figma review; no frontend acting mode is enabled yet.
Apply the audit migration before using these endpoints.

Staff and superusers can start support sessions. A superuser-only permission is
available for the later user and workspace management endpoints. Signing in as an
admin does not grant access to landlord data by itself: portfolio endpoints return
400, `Choose a workspace first.`

1. `POST /api/v1/platform/support-sessions/` with `organization` (workspace public
   UUID) and `reason` (5–300 characters after trimming). Starts are limited to ten
   per hour per administrator. Suspended workspaces cannot be opened.
2. Send `X-Dwella-Workspace: <workspace UUID>` on subsequent API calls. The resolver
   accepts it only for the authenticated admin's unended session whose expiry is
   still in the future. Sessions last four hours. The most recently started valid
   session for that admin and workspace supplies the reason. A malformed, unknown,
   expired or ended context returns 403 in the standard response envelope.
3. `/api/v1/accounts/me/` includes `access.acting_workspace` with the workspace
   `id`, `name`, `session_id`, `reason`, and `expires_at`. It is null without a
   selected workspace. Capabilities reflect owner access only while acting.
4. `GET /api/v1/platform/support-sessions/?active=true` lists the caller's live
   sessions with standard pagination. Omit the filter for history or use
   `active=false` for ended or expired sessions. Other admins' sessions are private.
5. `POST /api/v1/platform/support-sessions/<session UUID>/end/` ends the caller's
   session. Omit the workspace header when retrying an already ended session.
6. `POST /api/v1/accounts/logout/` ends all the caller's support sessions, revokes
   their API token and ends their Django session. Future frontend logout must call
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
transaction, so audit failure rolls back the business change. Session resolution
locks the support-session row through the request to serialize against leaving.
Audit events and support-session records are view-only in Django admin, including
for superusers; all session lifecycle changes go through the audited API.

Later phases add platform users, workspaces, audit browsing and platform dashboard
APIs. Suspending workspaces and landlord consent settings are outside Phase 1;
the console plan defines their remaining decisions. Nothing here enables deployment.
