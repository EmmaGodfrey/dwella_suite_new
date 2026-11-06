# External testing in the existing TEST application

7 November 2026. User-authorised external alpha preparation. The URL, database,
Compose project and production boundary remain those of the existing TEST setup.
No `/alpha` deployment is created. Manual test payments/proof review stay in scope;
online collections, automatic collections and payouts are excluded.

## Controls

`APP_ALPHA_TEST_ENABLED=true` is valid only with `APP_ENVIRONMENT=test`; other
environments refuse startup. It forces all three Lenco money-movement switches
off even if conflicting provider flags were supplied. Existing checkout/payout
service guards remain authoritative; no payment domain logic was changed.

In that explicit mode, normalised phone recipients can pass the old operator-only
TEST allowlist. Signed webhooks, exact-number CONNECT proof, verified account email,
active binding, live workspace/tenant access, optional-notice consent, STOP,
throttles, template approval and the customer-service window still apply. The
default TEST recipient policy remains restricted when the mode is off. There is
no added per-recipient database query.

TEST Compose distinguishes an unset email allowlist from an explicitly empty one.
An unset value retains the operator-inbox fallback; an explicitly empty value
permits direct intended recipients. `TEST_EMAIL_REDIRECT_TO` must also be empty.
The existing email backend still enforces sender identity and shared provider quota.
Mailbox proof, invitation identity and recovery throttles are unchanged.

The guided-tour mount is removed from the app shell, preserving stored progress
for later reuse. Optional WhatsApp remains in Get Started and Settings.

Alpha message commands dispatch user-triggered work but skip automatic reminder
and expiry sweeps over old test tenancies. The TEST scheduler should omit `billing`
and `renewals` for this initial supervised exercise. Manual invoice generation and
explicitly confirmed reminders remain available. Other environments keep existing
scheduled behaviour. Historic unsent notification rows must be reviewed/cancelled
with a retained reason before unrestricted recipient delivery is activated.

## Activation procedure

1. Validate source and publish a TEST-only release through normal CI gates.
2. Back up protected TEST environment files, runtime configuration and database.
3. Pause TEST dispatch workers during the short configuration cutover. Keep
   production and other projects untouched.
4. Enable the external-test switch; explicitly disable all money-movement flags;
   clear the test email redirect/allowlist; enable new operational email. Preserve
   SMS off, outbound OTP off, approved WhatsApp templates, consent and quiet hours.
5. Open self-service registration and email in the audited TEST runtime settings.
   Cancel reviewed historic unsent notifications with a reason; retain records.
6. Regenerate the restricted runtime environment and recreate only TEST app services.
   Restore the original environment/configuration and worker state if activation fails.
7. Verify public registration, link destinations, SMTP connectivity, payment flags,
   role restrictions, restricted DB privileges, worker/backup health and non-TEST
   container isolation. Genuine inbox/handset arrival still needs participant evidence.

## Tester pack

- [Handbook source](ALPHA_UAT_2026_11_07.md)
- [120-case source catalogue](uat/alpha_cases.json)
- [PDF/Word/workbook builder](uat/build_alpha_pack.py)

Generated PDF and editable Word handbook plus a results/bug workbook are under
ignored `output/alpha-test/`. They contain no tester identities or credentials.
Cases begin as Not run; shipped automated-test results do not pre-pass human UAT.

The organiser assigns roles/pairs, supplies dummy tax fields and sample files,
chooses a feedback channel/test window, and runs one genuine signup-to-WhatsApp
journey before inviting the wider group. SMS, real money movement, native outbound
OTP and unassigned roadmap features are excluded from the initial alpha.
