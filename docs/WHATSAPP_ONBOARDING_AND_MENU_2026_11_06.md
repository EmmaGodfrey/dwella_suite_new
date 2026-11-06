# WhatsApp onboarding and menu-first beta flow

6 November 2026. Current connection method: inbound CONNECT. The user chose to
restore this method while outbound authentication templates remain unavailable.

## Current connection flow

Get Started and Settings share the optional number/notice form. The user enters
their WhatsApp number, leaves notices off or explicitly opts in, then selects
**Connect WhatsApp**. The website prepares a ten-minute `CONNECT <code>` message.
**Open WhatsApp** opens the configured business number with that exact message.
After sending it from the entered number, the user returns and selects
**I've sent the message**. The website checks for inbound proof before asking the
backend to complete the connection; the backend independently validates the proof,
identity, number, expiry, attempts and current access.

Unreceived messages leave the connection pending; failures can be retried, and an
expired message requires starting again. Message text stays in component memory,
with zero-retention mutation results, and is cleared on reload/unmount. Existing
connections, MENU entry, disconnect, separate notice consent and SMS are retained.
This method does not depend on an authentication template or the outbound OTP flag.
The outbound OTP implementation remains dormant for later activation.

Restoration validation: production build, 45 Node checks, and 14 synthetic browser
scenario groups passed (manager Get Started, tenant Settings, mobile/light/dark,
exact chat message, unverified/failed confirmation, expiry, change number,
disconnect, notice consent and unavailable/retry states). No OTP API requests or
real sends occurred. Existing backend pairing/WhatsApp/notice/code tests passed:
142 passed, four PostgreSQL-only skips; Django check and Ruff passed against the
previously validated backend source, which this UI restoration does not change.

## Earlier outbound-code design (superseded in the UI)

## Result

Get Started and Settings → Notifications share the same optional connection flow:

1. Enter a WhatsApp number on the signed-in website.
2. Choose whether to receive optional notices. The checkbox starts unchecked.
3. Select **Send code on WhatsApp**.
4. Enter the six-digit WhatsApp code on the website and select **Verify and connect**.

No message back to Dwella is needed for verification. After connection, **Open
Dwella on WhatsApp** opens the business chat with MENU ready to send when the user
wants to use chat. Receiving an outbound verification code does not open an inbound
customer-service window. Optional connection notices require the separate opt-in.

The existing Business / Property / Unit setup and five workspace tasks remain intact.
The optional connection appears in the checklist surface without changing completion
or requiring phone verification to operate the workspace. Tenants use the same
component in Settings. SMS keeps its existing separate verification path.

Figma account-access page:
[number and opt-in](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=319-758),
[code entry](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=319-783),
[invalid code](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=319-801),
[connected](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=319-818).
These are editable layout references, not a claim of screenshot parity for every state.

## API and safeguards

`POST /api/v1/notifications/phone-verification/` starts verification with
`{"phone":"+260971234567","consent":false}`. A 202 response identifies the challenge,
expiry and resend delay; it never includes its code. Confirm on the same endpoint
with `{"complete":123,"code":"123456"}`. The normal response envelope is retained.
The caller must be an active, verified personal account. Completion rechecks current
workspace eligibility before binding the number.

- Six random decimal digits, keyed hash bound to the user, number, nonce and current
  identity proof; no plaintext code in the row, API response or audit event.
- Ten-minute expiry, five failed comparisons per challenge, 60-second account resend
  cooldown and user/number/IP request throttles. A new challenge consumes older ones.
- Confirmation locks the account and challenge; wrong-attempt counters commit before
  the validation response. Password/email/proof changes invalidate a challenge.
- STOP/disconnect invalidates pending links. An existing active account connection
  cannot be taken over by another account through this endpoint.
- Provider I/O occurs after the short database transaction. This personal endpoint
  owns its audited transactions and is exempted from the request-wide portfolio audit
  transaction; staff/support actors are rejected before writes.
- Provider calls do not retry ambiguous sends. A known rejection is unavailable;
  a timeout/unknown result stays reviewable and the user can enter a delivered code.
- Provider POSTs now reject redirects, preserving credential origin boundaries.
- Successful confirmation retains the real inbound timestamp instead of fabricating
  one. Ongoing notices follow the submitted opt-in, independently of account binding.
- Existing seven-day expired-link cleanup covers these rows. No financial ledger
  entries are created by verification.

Schema: notifications migration `0014_whatsapp_phone_codes` adds nonce, identity
stamp and transport metadata to the existing private phone-link table. Legacy
CONNECT handling cannot validate or complete an outbound-code challenge.

## Invoice PDF diagnosis

The sampled invoice requests on TEST failed document preparation because the linked
tenant lacked **TPIN and billing address**. The fallback text reached read status;
that did not mean the invoice PDF was delivered. Receipt and statement PDF requests
in the same pilot were delivered and read.

The reply now lists missing required tenant fields and directs a manager to complete
the tenant record, or a tenant to ask their manager. Document requirements remain
authoritative; no tenant facts are invented to make a PDF render. Completing those
real fields and requesting the invoice again remains necessary for this record.

## Menu behavior

Unknown messages return the role menu. An unsolicited attachment does not start a
payment proof or download provider media. Files are accepted within the relevant
guided draft; early payment attachments re-show the expected field. Repair details
precede photos. Existing validated amount/reference/reason fields remain usable.

MENU, CANCEL/BACK and STOP/UNSUBSCRIBE retain their established meanings. Cancelling
an unsubmitted draft does not submit it; STOP revokes connection/consent. Existing
durable reviewer buttons retain their current permission checks. **Create invoice
in Dwella** explicitly opens the website instead of an unsupported-action reply.

The beta uses existing buttons and lists. Native WhatsApp Flows, OCR, an AI assistant
and native invoice creation are not added by this work.

## Provider dependency and activation

The requested `dwella_verify_number` English authentication template uses a copy-code
button and ten-minute expiry. Meta rejected creation with HTTP 400, code 10,
subcode 2388185: this WABA does not have permission to create the template. A separate
read-only check reported account review APPROVED and business verification verified.
The provider restriction is unresolved; the account must not be described as unverified.

`APP_WHATSAPP_OTP_ENABLED` defaults false. After resolving eligibility and obtaining
approval, configure `WHATSAPP_OTP_TEMPLATE=dwella_verify_number`,
`WHATSAPP_OTP_LANGUAGE=en`, append `dwella_verify_number:en` to the existing approved
template list, then enable the OTP switch on TEST. Preserve the current eleven
approved templates, phone allowlist and all other channel/scheduler settings.
The UI shows an unavailable state while prerequisites are missing.

The request shape follows Meta's
[authentication-template API example](https://www.postman.com/meta/whatsapp-business-platform/request/6vkv46u/create-authentication-template-w-otp-copy-code-button).
Do not relabel a utility template or reuse a connection-notice parameter as an OTP.

## Validation and remaining handset evidence

The complete frozen-source suites passed: SQLite 1,649 passed / 34 PostgreSQL-only
skips, PostgreSQL 1,683 passed. Django check, Ruff and migration consistency passed.
The production frontend build, 45 Node checks and 15 browser scenario groups passed.
Browser checks use a production build with synthetic responses;
they do not send a verification code or establish handset delivery.

The existing live happy path remains proven: WhatsApp-origin proof, manager WhatsApp
confirmation, recorded payment/receipt and both notices read. Rejection, requests
for information, corrected resubmission, changed-access, repair-photo and requested
reminder handset branches require their own controlled pilot evidence. The code
tests cover those behaviors; they do not substitute for the phone pilot.

No production release, email activation or parked K1 reconciliation is included.

## TEST release verification

Released as `test-v2026.11.06.4` (`02df3c3`), with all CI gates and staging deployment
successful. Live source hashes and migration 0014 matched; the public TEST frontend
serves the new verification code and the API health check passes. Both existing
verified phone links and the two-phone allowlist remain intact. The OTP switch is
still off because Meta's authentication-template permission is unresolved.

After the restricted database-login transition, receipt and statement PDF rendering
still passed. Invoice rendering still correctly reports missing TPIN and billing
address; actual tenant details must be completed before retrying that PDF. These
read-only checks did not send messages or modify financial records.
