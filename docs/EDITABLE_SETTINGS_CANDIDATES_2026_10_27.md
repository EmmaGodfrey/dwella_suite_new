# Editable settings candidates

Source review on 2026-10-27, prompted by the replacement Handy address
`https://dwella.agents.handyagent.chat`. This is a proposal, not evidence that
the connection or the candidate settings have been changed or deployed.

## Immediate Handy findings

- The frontend agent address comes from `VITE_HANDY_AGENT_URL` at build time in
  `frontend/src/Services/handyAgent.js`; the widget loader address is hardcoded.
- `PlatformSettings` currently stores only the assistant on/off switch. The
  authenticated `/accounts/handy-agent/config/` endpoint returns only `enabled`.
- Frontend CSP explicitly allows the old agent origin. Updating a URL field alone
  would not make a new domain usable.
- Unauthenticated HTTPS checks from both the local machine and the deployment
  server reject the supplied new domain with a self-signed-certificate error.
  No TLS verification was bypassed, and no credentials or identity tokens were
  sent. Its API base path and widget compatibility remain unverified.

Recommended first change: system-admin-only assistant connection address, title
and suggested prompts in Settings. Publish permitted non-secret runtime values
through the authenticated config endpoint; keep signing secrets on the server.
Refresh the widget and clear old short-lived identity state on connection changes.
Restrict addresses to approved HTTPS provider origins and make CSP match that
policy; do not allow arbitrary script-loader addresses through the form. Preserve
the current environment-level disable switch and sensitive/public-page exclusion.
The new address should not receive tokens until its certificate and endpoint
contract are verified. Merely saving configuration should not send a chat message.

## Candidates found in the code

| Priority | Setting | Who edits it | Present state / implementation consideration |
| --- | --- | --- | --- |
| First | Handy connection address | System admin | Build-time frontend value plus server environment; needs runtime config and CSP coordination |
| First | Assistant title and starter questions | System admin | Hardcoded in `handyAgent.js`; straightforward bounded plain-text fields |
| First | Support email, phone/WhatsApp and help links | System admin | Useful shared contact configuration; publish only approved public fields, and define app/marketing consumers |
| Next | Email display name, reply-to and approved sender | System admin | Sender/reply-to environment settings; verified provider senders must remain authoritative |
| Next | Email routing allowances | System admin | Google 400 threshold and Resend daily/monthly caps are environment values; support provider-approved bounds and atomic quota reservations |
| Next | SMS sender identity and WhatsApp reminder template/language | System admin | Environment values in `backend/config/messaging.py`; only provider-approved identities/templates should activate |
| Next | Email/SMS/WhatsApp channel activation | System admin | Credentials and enable flags currently live in environment configuration; activation must require readiness/consent and preserve held-message handling |
| Next | Beta registration availability and email sequence pause | System admin | Environment-only registration/email gates; preserve generic recovery responses and do not automatically send a backlog when saved |
| Later | Beta opening date and countdown schedule | System admin | Backend date plus separately built marketing milestones; one authoritative value must reach signup copy, scheduler and marketing countdown together |
| Later | Defaults for new leases | Property manager, own workspace | Due day, late-fee/grace defaults and notice period could prefill drafts; existing leases/issued documents must retain their recorded terms |

Payment/withdrawal configuration is a separate candidate for Claude's review;
do not broaden this task into changing fee rules, balances or payment switches.

## Already editable; keep these in their existing place

- Business display name, contacts/address and time zone.
- Workspace reminder channels, days before due, overdue spacing/repeats and hour.
- Personal notification preferences and phone-specific consent.
- Platform quiet hours and automated-reminder preference.
- Outreach sender name/signature, offer, send window, pause and daily cap.
- Assistant on/off switch.

Production currently has a smaller release than develop/test. Availability of a
setting in local code is not a claim it is deployed to production; do not promote
newer modules merely to expose their future configuration.

## Configuration boundaries

Keep secret keys, SMTP passwords, signing secrets and provider callback secrets in
protected environment configuration under the existing project rule. Show their
configured/missing status without returning their values. Likewise keep database,
storage, CORS/CSRF/trusted origins, token issuer/audience and script-loading policy
under deployment control. A generic key/value settings editor is inappropriate.

Use typed backend validation, role-scoped APIs, atomic audit records and fresh
runtime reads with bounded request-local reuse. Separate test/production values.
Existing business and money records must keep their own recorded terms rather
than being silently rewritten when a default changes. Frontend additions should
extend the existing Settings surface through the agreed design review workflow.
