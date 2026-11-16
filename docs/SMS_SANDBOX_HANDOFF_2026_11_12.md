# SMS sandbox activation on TEST: handoff for Codex (12 Nov 2026)

Owner of the work: Codex (TEST server configuration and validation). Requested by the user
after Claude proved the Africa's Talking sandbox key works. No application code change is
expected unless the checks below find a defect.

## Current state

- The SMS path is already built and mock-tested: `backend/apps/notifications/phone_messaging.py`
  (`send_sms`), `provider_webhooks.py` (delivery, opt-out and incoming callbacks),
  `config/messaging.py`, consent, allowlist and runtime settings. See
  `docs/MESSAGING_PROVIDERS_2026_10_26.md` (section "SMS: Africa's Talking").
- It is OFF everywhere: `APP_SMS_ENABLED=false`, no Africa's Talking credentials on any server.
- Africa's Talking account: app "Dwella", live username `kupuzo`, Basic plan, wallet about
  ZMW 1.57. The dashboard says "Your account is not fully active yet". Live-app keys were
  rejected with 401 on 12 Nov. A support email is being sent by the user, who is also asking
  about a Zambia sender ID (cost and approval time unknown; third-party guesses only).
- The SANDBOX key works (checked by Claude on 12 Nov, 20:38 UTC):
  - `GET https://api.sandbox.africastalking.com/version1/user?username=sandbox` returned 200.
  - `POST /version1/messaging` (form-encoded, `username=sandbox`, `to=+254711000000`) returned
    201, `statusCode 101`, with a message ID. Sandbox simulates delivery; no real phone is texted.
  - Key fingerprint (first 8 hex of SHA-256, safe to share): `1C12E00D`.
  - Earlier keys were rejected; generating a new key invalidates the previous one. Do not
    regenerate the key.

## Task: switch SMS on in TEST, sandbox mode only

1. Obtain the key privately from the user (clipboard or their own paste into the protected
   server env). It must never be printed, committed, put in chat, or written to local files.
   Verify the fingerprint above before use. If it does not match, stop and ask.
2. Back up protected `.env.test` and the derived `.env.runtime` first (same protected
   cutover directory pattern used for the Resend cutover). Record the 19 non-TEST container
   identities and the env file hashes beforehand.
3. Set, through the existing protected-env route:
   - `AFRICASTALKING_USERNAME=sandbox`
   - `AFRICASTALKING_API_KEY=<key>`
   - `AFRICASTALKING_SANDBOX=true`
   - `AFRICASTALKING_CALLBACK_TOKEN=<random, at least 32 characters>`
   - `AFRICASTALKING_SENDER_ID=` left blank for now (no sender ID registered yet)
   - `APP_SMS_ENABLED=true`
   Preserve every other TEST setting: Resend-only email, no-money-movement flags, CONNECT
   flow, guided tour hidden, throttles, restricted runtime role.
4. Restart only the services that read these settings. Confirm all ten TEST services healthy,
   migrations still current, worker heartbeats fresh, restricted runtime credentials intact,
   and the 19 non-TEST container identities unchanged. Production is out of scope.
5. Callbacks: do not register the delivery or opt-out URLs in the Africa's Talking dashboard
   yet (sandbox reports are simulated). If you do configure them later, apply the Nginx and
   Gunicorn query-string redaction first, as the runbook requires.

## Checks before claiming it works

- **Empty sender ID.** `send_sms` always posts `from=<runtime sms_sender_id>`, which is an
  empty string while no sender ID is registered. Claude's probes never reached that code with
  a valid key, so it is UNVERIFIED that the sandbox accepts `from=`. Test it. If the sandbox
  rejects an empty `from`, change `send_sms` to omit the field when blank, with a regression
  test, in a small focused commit.
- **Zambian numbers in the sandbox.** Claude's successful call used a Kenyan test number.
  Confirm a `+260` number is accepted by the sandbox and what it returns.
- Send ONE simulated SMS through Dwella's real queue (a consenting TEST tenant with a normal
  `+260` number, SMS consent recorded, number allowed by the TEST external-alpha rules), not by
  a direct HTTP call. Confirm: row state `sent`, provider ID stored, no automatic resend, the
  body identifies Dwella and says to opt out in Settings > Notifications, and Messages history
  shows the status.
- Read the response handling: `statusCode` 101 or 102 accepted; other codes become
  `ProviderRejected("at_<code>")`.
- STOP wording: a sender name cannot receive replies, so do not advertise "reply STOP" unless
  two-way service is provisioned.
- SMS recipients are only people who have given phone-specific SMS consent. Do not send to any
  other number, and do not run bulk or reminder sweeps. Automatic reminders stay paused for the
  supervised alpha.

## Out of scope

- Live credentials, real SMS, any production change, and a sender-ID request (the user is
  handling the account and sender ID with Africa's Talking support).
- Callback registration in the dashboard, message-credit or top-up work, pushes to main.
- Do not touch Claude's payment modules or the original `billing/views.py` and
  `portal/tests.py` diffs. `docs/OUTREACH_PLAN.md` is an unrelated local change.

## Rollback

Restore the backed-up `.env.test` and `.env.runtime` and restart the same services, or set
`APP_SMS_ENABLED=false`. Sandbox sends are simulated, so there is nothing to refund or retract.

## Later, once Africa's Talking fixes the live account

Live swap: `AFRICASTALKING_USERNAME=kupuzo`, a live key, `AFRICASTALKING_SANDBOX=false`, an
approved `AFRICASTALKING_SENDER_ID`, a funded wallet, then a controlled real-number test, and
the `APP_OUTBOUND_PHONE_ALLOWLIST` rules. The user confirms each step.
