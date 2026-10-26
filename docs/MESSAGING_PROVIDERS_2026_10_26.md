# Messaging provider setup — 26 October 2026

Implementation is local and sending remains disabled by default. No real provider
send, deployment, account purchase or sender registration is part of these checks.
Run migrations before enabling any provider. Existing held requests are never
released automatically when credentials are added: cancel and compose again.

## Email: Google first, then Resend

Every Django mail caller goes through the same router when explicitly enabled.
The existing recipient guard wraps the router, so test redirection also applies to
Resend, including To/Cc/Bcc. Configure a verified Dwella domain for Resend; do not
use a gmail.com From address with Resend.

The budget is shared within one deployment/database. If test and production use
the same Google or Resend account, split their configured allowances so their
combined usage fits that account's limits, or use separate sending accounts.

Server environment values (place real secrets only in the protected root `.env` or
the environment's protected server configuration):

```dotenv
APP_EMAIL_ROUTING_ENABLED=false
APP_EMAIL_GOOGLE_LIMIT=400
RESEND_API_KEY=
RESEND_FROM_EMAIL=
RESEND_DAILY_LIMIT=100
RESEND_MONTHLY_LIMIT=3000
APP_MESSAGING_EMAIL_ENABLED=false
```

Keep `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` and the existing
Google SMTP credentials. Routing replaces the backend internally when enabled;
do not set EMAIL_BACKEND to the router itself. Resend quotas are configurable to
match the purchased plan. Defaults conservatively target the free plan. Google's
400 is Dwella's budget, not a Google-guaranteed allowance. Other mail sent manually
from that Google account is outside our count.

The budget counts recipients, including cc/bcc and uncertain attempts. Hourly
buckets retain up to 25 hours conservatively; 35-day counter retention supports
calendar-month Resend quotas without retaining per-email payloads. Reservation is
atomic across workers. Production PostgreSQL uses a separate connection to the
same database (`email_quota`) so legacy synchronous account-email transactions
cannot retain the global quota lock during SMTP or roll its reservation back.
SQLite supports isolated local checks, not concurrent production routing.

An email over the Google budget routes to Resend before sending. No fallback is
attempted after a timeout/uncertain send. Quota exhaustion defers reminder jobs;
unknown reminder outcomes need review. The signing outbox stops automatic retries
after an uncertain routed send rather than risk sending again through another
provider. Google acceptance and Resend API acceptance are not confirmed delivery;
email delivery/bounce webhooks are not implemented in this increment.

Before first activation, reconcile recent Google usage or wait for the allowance
window to clear; the new global counter cannot reconstruct old account mail.

## WhatsApp: direct Meta Cloud API

Use a Meta Business Portfolio and WhatsApp developer app. Meta verification is
currently pending. Start with Meta's test number and designated recipient; later
register the business number, display name and billing. Never delete an existing
WhatsApp account as an automatic setup step; check the applicable migration or
coexistence path first.

```dotenv
APP_WHATSAPP_ENABLED=false
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_BUSINESS_ACCOUNT_ID=
WHATSAPP_APP_SECRET=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_GRAPH_VERSION=v24.0
WHATSAPP_RENT_TEMPLATE=
WHATSAPP_TEMPLATE_LANGUAGE=en
APP_OUTBOUND_PHONE_ALLOWLIST=
```

Use a server-side production token with the necessary WhatsApp messaging
permissions; the developer dashboard's temporary token is only for initial tests.
All IDs/secrets must belong to the same business account and phone number.

Webhook path: `/api/v1/notifications/webhooks/whatsapp/`. The test site's public URL
is `https://app.dwella.properties/test/api/v1/notifications/webhooks/whatsapp/`.
It handles Meta's GET challenge and verifies the raw POST body with HMAC-SHA256
using the app secret. Subscribe to `messages`. Account and phone IDs are checked
before processing events. Confirm the selected Graph version is available for
the app when configuring it.

Submit an English **utility** rent reminder with these five body parameters:

> Hello {{1}}, {{2}} reminds you that invoice {{3}} has {{4}} outstanding and is due
> on {{5}}. Check Dwella for details. To stop WhatsApp reminders, reply STOP.

Parameter order: tenant name, workspace name, invoice reference, currency and
outstanding balance, ISO due date. Set WHATSAPP_RENT_TEMPLATE only after approval,
using its exact name and language. Unconfigured templates are excluded from
scheduled reminder generation. Lease-signing WhatsApp templates are not wired in
this increment; signing email continues through its existing outbox.

Custom on-demand notices use free text only within 24 hours of an authentic tenant
inbound message. Outside that window they are held with
`whatsapp_reply_window_closed`, rather than disguising arbitrary text as an
approved utility template. The platform is send-only: it stores the last inbound
timestamp and consent changes, not a chat history.

Tenant Settings opt-in records the exact linked phone, actor, source and time.
Changing the phone does not copy consent. STOP/UNSUBSCRIBE and the Settings switch
revoke permission business-wide for that exact number. A subsequent greeting does
not automatically resubscribe the tenant. An existing SMS preference alone does
not count as recorded phone consent.

## SMS: Africa's Talking

The user approved preparing Africa's Talking on 26 October. Create an account,
obtain the application username/API key, register the desired sender name for
Zambia and fund the account. Sandbox credentials and live credentials differ.

```dotenv
APP_SMS_ENABLED=false
AFRICASTALKING_USERNAME=
AFRICASTALKING_API_KEY=
AFRICASTALKING_SENDER_ID=
AFRICASTALKING_CALLBACK_TOKEN=
AFRICASTALKING_SANDBOX=true
```

Generate a random callback token of at least 32 characters. Configure HTTPS URLs
in the provider dashboard, with `?token=<secret>` on each:

- `/api/v1/notifications/webhooks/sms/delivery/`
- `/api/v1/notifications/webhooks/sms/opt-out/`
- `/api/v1/notifications/webhooks/sms/incoming/` (if two-way SMS is provisioned)

Add `/test` before `/api` on the test site. The token is a bearer credential,
not an Africa's Talking body signature. Apply the supplied Nginx and Gunicorn
query-redaction configuration before enabling callbacks; do not paste a complete
credential-bearing callback URL into tickets, messages or screenshots. Rotate the
token if exposed. Ensure any additional proxy/access logging also omits query
strings. Provider IP restrictions can supplement authentication when confirmed
with the provider; no guessed IP ranges are trusted.

The adapter uses form encoding, explicitly selects sandbox/live host, and checks
each recipient result even when the HTTP response is 200. Gateway acceptance is
stored as `sent`; only a successful delivery report sets `delivered`. An early
report receives 503 while a send is awaiting its provider ID so it can be retried.
There is no automatic resend after an uncertain network outcome.

Every SMS identifies Dwella and directs recipients to Settings > Notifications
to opt out. Sender names may not accept replies: do not advertise reply STOP
unless two-way service is provisioned. Authenticated provider opt-out callbacks
and STOP messages on a provisioned two-way route are also handled. Long SMS can
cost multiple segments, including the opt-out text.

## Delivery evidence and controlled activation

Messages shows accepted, delivered, read (WhatsApp when reported), failed, held,
cancelled and needs-review states. Platform admins can see failure codes in the
history table. Duplicate/out-of-order callbacks do not regress delivered/read
evidence, and callbacks never trigger a resend. No growing callback snapshot/chat
table is written. Consent has default-deny PostgreSQL row security alongside
existing private message tables.

On test, outbound phones must appear in APP_OUTBOUND_PHONE_ALLOWLIST. This is
independent of the email allowlist. Keep the existing TEST_EMAIL_REDIRECT_TO for
real reminder and signing-email tests. Save the tenant's explicit consent and
enable only the provider being tested. Exercise new messages; do not release old
held requests. Credentials/account setup, a controlled live send and provider
delivery report are still required before claiming end-to-end delivery works.

## Validation

Focused tests cover recipient guards, global routing, quotas/retention, attachments,
uncertain sends, consent changes, missing configuration, test-only phone allowlists,
Meta signatures and verification, callback account/phone isolation, malformed
payloads, throttling, delivery races and duplicate/out-of-order reports. PostgreSQL
tests cover independent reservations, concurrent quota claims and row security.
The admin list query-count check compares one message with a full 25-row page.

Validation results:

- Full SQLite backend: **1,035 passed, 22 skipped**. The first attempt encountered
  Windows temp-folder permissions; rerunning with a workspace-specific basetemp
  passed. Skips include PostgreSQL-only checks.
- PostgreSQL 17 common/notifications/signing-outbox checks: **195 passed**.
  Final focused checks after SMTP reuse and consent-race refinements: **22 passed**.
  The database was an isolated, loopback-only local test instance.
- Django system check, Ruff and migration drift check passed.
- Frontend production build and **25** existing Node checks passed.
- Synthetic Playwright checks passed for admin provider status, delivery failure
  codes/status filtering, tenant opt-in save, and 390px layout without overflow.
  Consent saves submit only changed fields, preventing an unrelated settings save
  from silently resubscribing a channel whose preference was stale in the browser.
- The admin list uses equal query counts for one delivery and a full 25-row page.

These are mocked provider and local database checks. Real reminder and signing
emails on test, SMS delivery, Meta template approval and WhatsApp delivery/read
receipts remain to be verified after credentials and test deployment are ready.

References: [Meta Cloud API](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api),
[WhatsApp policy](https://business.whatsapp.com/policy),
[Resend sending API](https://resend.com/docs/api-reference/emails/send-email),
[Africa's Talking APIs](https://developers.africastalking.com/),
[Africa's Talking delivery status explanations](https://help.africastalking.com/en/articles/742491-why-did-my-messages-fail).
