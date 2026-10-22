# Platform admin console — plan

Written 22 October 2026 for Codex to carry out. Owner: the platform admin (the user).

## What the user asked for

> User management for admin… basically all super admin functions. Same sidebar, just add
> other stuff for admin. Admin should be able to do every action on behalf of landlords
> and whoever. Design in Figma first, follow our design standards.

So:

- One app, one sidebar. A platform admin sees the usual landlord groups plus a
  **Platform** group with the admin-only pages.
- The admin can manage every user and workspace on the platform.
- The admin can open any landlord's workspace and do anything that landlord can do:
  add properties, record payments, run billing, handle maintenance and so on.
- **Figma first.** Design every new screen in the Dwella Figma file, wait for the user's
  review, then build.

## How things stand (checked on develop at ce87a64)

| Area | Today | Problem |
| --- | --- | --- |
| Who is an admin | `is_staff` or `is_superuser` → persona `platform_admin` (`apps/common/permissions.py:get_user_access`) | Works, but staff and superuser are treated the same |
| Reading data | `OrganizationScopedModelViewSet.get_queryset` returns **every organization's rows mixed together** for staff | No way to look at one landlord's portfolio. Lists across landlords are confusing |
| Writing data | `CanManagePortfolio` needs an active membership, and `can_manage_properties` is `False` for admins | Admins can view but can't act |
| Creating records | `perform_create` saves `organization=self.get_organization()`, which is `None` for admins | Would fail or create orphan rows |
| Workspace context | `apps/maintenance/services.py` reads `request.organization`, but nothing sets it | Ready for a context mechanism |
| Organizations API | `OrganizationViewSet` only lists the caller's own memberships | No platform-wide list |
| Users API | Only `me/` endpoints | No user management at all |
| Identity checks | `IdentityVerification` model, with users submitting from Profile | Nobody can approve or reject them |
| Audit | `AuditEvent` model and Django admin registration, plus a request-id middleware | **Nothing writes events** |
| Auth | DRF `TokenAuthentication` (one token per user) and sessions | Deleting a user's `Token` signs them out everywhere |
| Frontend | `shared/navigation.jsx` personas; the Platform group currently holds only Beta signups; the sidebar org card is kept (user's request) | The org card is the natural place for a workspace switcher |
| Requirements | `docs/DWELLA_PROPERTY_MANAGEMENT_REQUIREMENTS.md` §3.1: admins must not access tenant financial or private data unless support access is **granted and audited** | Act-on-behalf has to be explicit and audited (see below) |
| Figma | Page "Admin (Platform)" already has Landlords, Landlord detail, Payments/exceptions, Audit log, Messaging, Settings and Admin Properties (x ≥ 3120, Properties at x = 12480) | Start from these. Don't redesign from zero |

## Key decision: act *in a workspace*, not *as a user*

The admin picks a workspace ("Acting in Mwale Properties") and every landlord screen
then works against that workspace, with full owner rights. We do **not** log in as the
landlord.

Why this approach:

- It covers "do every action on behalf of landlords". Every landlord action lives in an
  organization-scoped endpoint.
- The admin's own identity, 2FA and session stay in place. Every change is recorded
  as "done by <admin> in <workspace>", never disguised as the landlord.
- It meets the audited support-access rule in requirements §3.1.
- Tenants have no portal yet (deferred), so acting on behalf of a tenant means working
  in their landlord's workspace (record their payment, log their repair request).
  Once a tenant portal exists, re-check whether a read-only "view as tenant" is needed.

How it works:

1. **Entering a workspace.** The admin chooses it from the sidebar org card (it becomes
   a switcher for admins) or clicks "Open workspace" on a workspace's detail page. A short
   dialog asks for a **reason** (required, 5–300 characters, e.g. "Beta onboarding call").
   This creates a `SupportSession` (admin, organization, reason, started_at, ended_at,
   expires_at with a 4-hour default).
2. **Sending the context.** The frontend sends `X-Dwella-Workspace: <organization public_id>`
   on every API call while a session is active. Store the workspace id in
   `sessionStorage`, never in the URL.
3. **Resolving it on the backend.** A single resolver (middleware or a mixin used by
   `OrganizationScopedModelViewSet`, `APIView` reports/dashboard/notifications/onboarding)
   sets `request.organization`. The header is accepted **only** when the user is a
   platform admin **and** has an unexpired, unended `SupportSession` for that organization.
   Otherwise return 403 with the standard envelope. For non-admins the header is ignored
   and their membership decides, as today.
4. **Permissions.** A platform admin with a resolved workspace gets owner-level access
   (view + manage + organization settings). An admin **without** one gets the platform
   pages only. The landlord endpoints return 400 "Choose a workspace first" instead of
   today's mixed all-organization lists. Remove the staff bypass in
   `OrganizationScopedModelViewSet.get_queryset` and in the `has_object_permission`
   methods, and route everything through the resolved organization.
5. **Auditing.** Every write (non-safe method) made under a support session writes an
   `AuditEvent` with actor, organization, action, resource type and id, request id, and
   `metadata.support_session` / `metadata.reason`. Entering and leaving a session are
   audited too.
6. **Visible to everyone.** A persistent banner at the top of the content area reads
   "You're working in <Workspace> as Dwella support · Reason · Leave", using the navy
   tone rather than red. Records created during a session show "by Dwella support" in
   activity/history views where they already show an author.
7. **Leaving.** "Leave" ends the session and returns the admin to the platform dashboard.
   Sessions also end on expiry or sign-out.

Optional, recommended later: a landlord setting "Allow Dwella support to open my
workspace". Leave it out of this build (during beta every workspace allows support),
but keep it in mind when designing the model.

## Admin roles

- `is_staff` = platform admin: everything in this plan.
- `is_superuser` additionally: grant or revoke platform admin, permanently delete users,
  and hard-delete workspaces. Every other destructive action is a soft action
  (deactivate or suspend) and is available to all staff.
- An admin can never deactivate, demote or delete themselves, or remove the last
  superuser.

## Sidebar

Same `AppSideNav`. For `platform_admin`:

- **Platform** group (always visible): Admin dashboard (`/dashboard` already maps to
  "Administration"), Workspaces, Users, Identity checks, Beta signups (exists), Audit log.
- **Overview / Portfolio / Operations** groups (Get started, Dashboard, Reports,
  Properties, Tenants, Leases, Billing, Maintenance) show **only while acting in a
  workspace**, and then behave exactly as for an owner.
- Org card: for admins it shows "Platform" or the current workspace, and opens the
  workspace picker (search, recent workspaces).
- Update `canAccessPath`, `getNavigationItems` and `getPageMeta` to match.
  `shared/access.js` reads `access` from `/me/`; extend the backend `get_user_access`
  response with `acting_workspace` (id, name, session id, reason, expires_at) so the
  frontend never guesses.

## Phases

Each phase is a backend + frontend slice with themed commits (separate API / hooks /
screens commits, never one big commit). Work on `develop`. **Don't push to main and don't
deploy** unless the user asks.

### Phase 0 — Figma (blocks all frontend work)

Read `.agents/skills/dwella-impeccable-ui` and `dwella-taste-ui` first. Then, in the Figma
file `aHlQPzHBsvGR4rNoabRQyW`, page "Admin (Platform)":

- Reuse the Foundations variables and components (Text Field, status pill, drawers,
  tables, sidebar).
- Visual rules: white sidebar, navy `#1D417E` only for primary actions and key figures,
  green `#2BA053` (`#22854A` for buttons) for positive and money-in. Not too blue.
- Layout rules: edge-to-edge content with 32px gutters, no centred max-width wrappers,
  rem type, Figtree UI with Montserrat display.
- Update the existing Landlords and Landlord detail frames into **Workspaces** and
  **Workspace detail**, and add:
  1. Sidebar for admin: Platform group, plus the org card as a switcher (both states:
     platform and acting).
  2. Workspace picker popover, and the "Open workspace" reason dialog.
  3. The acting banner on top of a landlord screen (e.g. Billing), in light and dark.
  4. Users list (search, filters: role/persona, status, verified, 2FA, workspace).
  5. User detail: profile, memberships, security (2FA, last login, sign-out-everywhere),
     identity verification, recent audit events, plus the actions menu.
  6. Create user drawer (landlord with a new workspace / member of an existing workspace /
     platform admin).
  7. Change role / add to workspace drawer.
  8. Identity checks queue and review drawer (approve or reject with a reason).
  9. Workspace detail: summary figures, members, properties, recent activity, plus
     actions (open workspace, suspend, transfer ownership).
  10. Audit log (filters: actor, workspace, action, date; detail drawer; CSV export).
  11. Admin dashboard update (signups, active workspaces, open support sessions, pending
      identity checks, recent audit events).
  12. Confirmation dialogs for destructive actions, and empty/loading/error states.
- **Stop and get the user's review** on these frames. Update Figma with their feedback
  before starting frontend code. Backend phase 1 can proceed meanwhile.

### Phase 1 — Backend foundation: workspace context, permissions, audit

- `apps/audit/services.py`: `record_event(request, action, resource=None, organization=None, **metadata)`.
- `SupportSession` model (in `apps/audit` or a new `apps/platform`) with migration and
  Django admin registration.
- Workspace resolver plus `IsPlatformAdmin` / `IsPlatformSuperuser` permissions.
- Rework `get_user_access`, `CanViewPortfolio`, `CanManagePortfolio`,
  `CanManageOrganization` and `OrganizationScopedModelViewSet` so they use the resolved
  organization. Cover the APIViews: dashboard summary, reports, notifications,
  onboarding, smart-invoice settings, maintenance services.
- Endpoints: `POST /api/v1/platform/support-sessions/` (start, takes a reason),
  `POST …/{id}/end/`, `GET …/?active=true`. Add `acting_workspace` to `/me/`.
- Throttle session starts.
- Tests: admin without session → 400/403 on landlord endpoints; admin with session can
  CRUD in that org only; header for a different org → 403; expired/ended session → 403;
  a non-admin sending the header → ignored (still only their own org); landlord access
  unchanged (run the whole suite); every write under a session creates an `AuditEvent`
  with the reason.

### Phase 2 — Users

API under `/api/v1/platform/users/` (staff only, paginated, standard envelope):

- List/search (name, email, phone), filters (persona/role, active, staff, 2FA, identity
  status, workspace), and detail including memberships.
- Create user: landlord (also creates a workspace through the existing onboarding
  service), member of an existing workspace with a role, or platform admin (superuser
  only). New users get no password and a set-password email, reusing the
  beta sign-in-details email/link flow in `apps/marketing/emails.py` and
  `/login?reset_uid…`.
- Edit name, email (unique, block disposable domains as today) and phone.
- Deactivate/reactivate (`is_active`). Deactivating also deletes their `Token`.
- Send password reset link. Sign out everywhere (delete `Token`). Reset 2FA (remove
  `TwoFactorDevice`).
- Memberships: add to a workspace, change role, remove. Never remove a workspace's last
  owner.
- Grant/revoke platform admin (superuser only). Permanent delete (superuser only, only
  after deactivation, typed confirmation).
- Identity checks: `/api/v1/platform/identity-verifications/` queue, approve, reject
  with a reason (and email the user if email is configured).
- Audit every action. Tests for each permission edge: non-staff 403, staff vs
  superuser, self-protection, last-owner and last-superuser guards, validation errors,
  no user enumeration in public flows.

Frontend: `/admin/users`, `/admin/users/:id`, `/admin/identity-checks`, hooks in
`src/Services/`, following Figma.

### Phase 3 — Workspaces

API `/api/v1/platform/workspaces/`:

- List with summary figures (properties, units, occupancy, active leases, outstanding
  balance, last activity, owner) and search/filter (active, suspended, created date).
- Detail.
- Create a workspace for an existing or new landlord (reuse onboarding).
- Edit the profile (same fields as the owner's organization settings).
- Suspend/reactivate (`is_active=False`). Members of a suspended workspace can sign in but
  see a "workspace suspended, contact Dwella" state, and API writes are refused. Decide
  whether reads are refused too, and document it.
- Transfer ownership. Members (reuse the phase 2 membership actions).
- Hard delete: superuser only, typed confirmation, only when suspended.

Frontend: `/admin/workspaces`, `/admin/workspaces/:id` with "Open workspace" → reason
dialog → acting mode.

### Phase 4 — Acting mode in the UI

- Workspace picker on the org card. The reason dialog. Store the active session in
  `sessionStorage` and send the `X-Dwella-Workspace` header from the axios instance in
  `src/Services/`.
- Clear all TanStack Query caches when switching or leaving a workspace, so no data
  leaks between workspaces.
- Banner, sidebar group visibility, and handling for 403 "session expired" (return to
  the picker with a message).
- Smoke-check every landlord flow while acting: setup, properties/units, tenants, leases
  activate/end, billing generate/record payment/reverse/void, receipts print,
  maintenance, reports CSV, notifications.

### Phase 5 — Audit log

- API `/api/v1/platform/audit-events/` with filters (actor, workspace, action, resource,
  date range, support session) and CSV export.
- Also start recording important landlord-side events that aren't under support
  sessions: sign-in, 2FA changes, payment recorded/reversed, invoice voided, lease
  ended. Keep it to a short list.
- Frontend `/admin/audit-log`, plus the "recent activity" panels on user and workspace
  detail.

### Phase 6 — Admin dashboard

Replace the current admin variant of `/dashboard` with platform figures: beta signups by
status, workspaces (active/suspended/new this week), users, open support sessions,
pending identity checks, collections recorded this month across the platform, and recent
audit events.

### Later (not in this build)

- Integrations admin: ZRA, mobile money, SMS/WhatsApp credits, payouts, exceptions. The
  user said integration pages come later.
- Platform messaging and announcements.
- Subscriptions and plans.
- Landlord opt-in for support access.
- "View as tenant", once the tenant portal exists.

## Done means

- Backend: `python manage.py check`, `ruff check .`, migrations consistent, and the
  **full** pytest suite passing, with new tests for every permission and failure path
  above.
- Frontend: production build passes. Browser-check the admin pages and acting mode at
  desktop and mobile widths, light and dark, and at 67%/200% zoom.
- `docs/OPEN_BETA.md` (or a new `docs/ADMIN_CONSOLE.md`) describes how to use the
  console and the security model.
- Shared memory `.agents/memory/build-progress.md` is updated after each phase.
- Nothing pushed to `main`, nothing deployed, until the user says so.
