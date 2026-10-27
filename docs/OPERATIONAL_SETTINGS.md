# Operational settings

Implemented locally across 2026-10-27/28 following approval of the editable-settings
shortlist, excluding Resend. No provider credentials, live sending switches,
deployed test/production databases or deployed applications were changed by this task.

## Settings surface

System admins can edit:

- **Assistant:** approved HTTPS connection address, title and up to six suggested
  questions. Existing availability control remains separate.
- **Support:** email, phone, WhatsApp number and HTTPS help link. These appear in
  Settings for all roles and in the marketing-site footer.
- **Messaging:** sender display name, approved sender address, reply-to, daily
  SMTP recipient allowance, email notices/reminders activation, approved SMS
  identity and WhatsApp template/language, and channel activation.
- **Beta:** registration availability, beta-email pause/resume, beta opening and
  public launch dates, three countdown offsets and the local sending hour.

Existing property-manager and tenant roles, workspace preferences, outreach
settings and financial records are preserved. Resend settings, credentials and
activation are not exposed or changed. No payment-provider behavior is changed.

## Runtime contract

`GET/PATCH /api/v1/platform/runtime-settings/` is restricted to system admins.
Only explicitly typed fields are accepted; unknown keys, credentials and private
connection-verification fields cannot be submitted. Partial saves lock one
settings row briefly and commit together with an audit event. GET does not create
records. Values fall back to environment defaults until saved; no process-wide
settings cache can become stale across workers. PostgreSQL row security and a
revoked assistant-role grant protect the settings table independently of API
permissions.

`POST /api/v1/platform/runtime-settings/assistant-check/` checks the saved API address's `/me/` endpoint
without a token or cookies. The address must use an approved HTTPS origin, have
no URL credentials/query/fragment and resolve exclusively to public addresses.
The connection pins the checked IP, verifies TLS against the original hostname,
disables proxies and redirects, and runs outside the database transaction. A
changed address during the check invalidates the result. This checks HTTPS and
endpoint reachability; it does not claim a successful authenticated agent chat.

Changing an assistant address disables the assistant and invalidates saved
verification. A successful check does not enable it. Approved legacy environment
connections retain their deployment contract. The authenticated config endpoint
returns only permitted widget metadata to eligible accounts; unavailable users
get `enabled: false`. The widget reads that metadata at runtime, refreshes its
provider dataset and clears cached/pending short-lived identities when it changes.
The deployment-level widget disable flag and sensitive/public-page exclusions
remain in effect. The CSP adds only the explicitly requested new Handy origin,
without allowing arbitrary hosts or script URLs.

The new domain initially failed normal certificate validation during source
review, then passed independent workstation/server checks later on 2026-10-27.
Its bare root returns404; the agent base address is
`https://dwella.agents.handyagent.chat/agent`, with an unauthenticated identity
response at `/agent/me/`. The connection check uses that API suffix and validates
the bounded JSON identity response. Authenticated chat/host actions and live
activation remain untested; no identity token, cookie or message was sent.

## Delivery behavior

The existing outbound recipient guard stays outermost. For SMTP deployments,
runtime sender defaults and the shared recipient budget run underneath it. The
budget uses the existing independent PostgreSQL quota connection and short global
reservation lock before network I/O. Conservative hourly counters cover up to
25 hours and retain failed/uncertain reservations. Ordinary SMTP never acquires
a new cross-provider fallback. Existing optional routing remains unchanged.

The daily allowance can be lowered within the deployment/provider ceiling
(at most 400 through this form). Sender addresses and SMS identities come from
deployment-approved identities; WhatsApp activation requires an approved
template/language plus configured credentials. Secrets remain in protected
environment configuration. Phone-specific opt-in, opt-out, tenant scope and fresh
actor authority still apply. Saving configuration sends no message and does not
release old held requests. Uncertain SMTP outcomes remain distinguishable from
safe retries, including signing-mail handling.

Beta email scheduling reads the same opening date, hour and offsets as the UI.
Resuming email or changing its schedule records a boundary so missed historical
steps are not silently backfilled. Existing email history and manually issued
access links are preserved; system admins retain explicit send-access actions.
Custom countdown offsets produce matching subject/date wording.

## Public consumers and rollout

`GET /api/v1/marketing/configuration/` returns only public support contacts,
opening/launch dates and registration availability. It has an independent
read-only throttle and no-store response. The app's login/registration copy and
beta signup timeline use runtime values. The sibling `dwella-site` application
shares one configuration fetch across its banner, countdown, timeline, signup
confirmation and footer, refreshes on focus/every minute, and renders an honest
undated state until dates are available. No stale date is embedded in SEO copy.

Deploy the suite backend/migration and matching app frontend before the marketing
consumer. Production currently contains less code than develop/test; this task
does not authorize promoting unrelated modules. Test first with recipient guards
retained, review saved values, and separately approve any live channel activation.

Optional approved identities are configured through `APP_APPROVED_EMAIL_SENDERS`,
`APP_APPROVED_SMS_SENDERS`, and `APP_APPROVED_WHATSAPP_TEMPLATES` (comma-separated
`template:language` pairs). Existing deployed identities remain usable. Trusted
assistant origins and CSP are deployment policy. Default public contacts and
launch date can be bootstrapped with `APP_SUPPORT_EMAIL`, `APP_SUPPORT_PHONE`,
and `APP_LAUNCH_DATE`.

## Validation

Security tests cover system-admin access, unauthenticated/ordinary-account
denial, malformed/unknown fields, header injection, approved identities,
activation readiness, throttling, audit rollback, stale connection checks,
certificate/redirect/private-address denial, IP pinning and no network under
settings locks. PostgreSQL covers settings privacy and quota concurrency.

Read-only public configuration performs one row read. Message confirmation uses
the same **9 queries for 1 and 25 recipients** after hoisting configuration out
of recipient construction; per-message sending still rechecks current authority
and channel availability. Operational settings never run external I/O under the
configuration row lock.

Browser checks use intercepted APIs/providers, independent of real database and
permission tests. They cover failed-save draft retention, validation, provider
readiness errors, assistant refresh/token clearing, roles, shared marketing
configuration, canonical Property-manager signup, and desktop/mobile/light/dark
layouts. No real messages, signups or financial transactions are test evidence.

Final validation on 2026-10-28:

- Full PostgreSQL17 backend suite: **1,114 passed**. Focused PostgreSQL boundary
  checks: **48 passed**; earlier broader provider/permission checks also passed.
- Broad SQLite run:1,085 passed/22 skipped, with two assertions for the old SMTP
  wrapper order. Both assertions were corrected; the relevant SQLite rerun
  passed55 checks. Expanded late API/mail/schedule checks passed84/1 skipped,
  followed by42/1 skipped for the final bounded Handy identity handshake.
- Django system check, Ruff and migration consistency: passed.
- App production build,25 Node checks, marketing lint and client/SSR/prerender
  builds: passed.
- Synthetic browser interaction, role, failed-save, desktop/mobile/theme,
  assistant-refresh and shared marketing-config checks: passed.
- Real read-only connection probe: the new `/agent/me/` endpoint passed the
  pinned-IP/default-TLS verifier without an identity token or cookie. This is not
  an authenticated chat, host-action or message-delivery acceptance test.

The focused late checks cover the same-day beta resume boundary, sender/origin
approval revocation and final endpoint handshake. No push or deployment was
performed. The suite and sibling marketing work are committed on local develop
branches; only unrelated business-cost/proposal edits remain outside this task.
