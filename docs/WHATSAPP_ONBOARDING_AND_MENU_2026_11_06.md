# WhatsApp onboarding and menu-first beta flow

6 November 2026. Implemented locally; deployment and real verification-code delivery
are separate from the validation below.

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
