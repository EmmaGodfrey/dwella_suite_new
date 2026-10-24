# Account access, email verification and extensible tours

Requested 24 October 2026. Preserve existing page structure and the Business → Property → Unit setup/checklist. Complete the account-access module before moving to the other agreed MVP modules. The tour must grow as new modules are added.

## Design review

Editable Figma page: [Account access & setup — MVP](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=192-107).

Twenty-one proposals cover email verification/waiting/confirmation/expired/delivery failure, password-reset sent/expired, tenant new-account/existing-account/expired invitations, existing setup, optional tour welcome, anchored step, mobile guidance, resume/replay, newly added module guidance, completion, legacy-account verification prompt and stronger two-factor-removal confirmation. Existing auth/components/checklist are reused; no existing page is restructured. The user approved these designs on 25 October 2026: "designs are good continue".

## Backend implementation contract

1. New self-service registrations require mailbox verification before workspace setup/portfolio access. Existing accounts are not silently marked verified or abruptly locked out; their current access is preserved while an optional verification prompt is introduced. Proof is bound to the current email, not just a boolean. Account, password-recovery and verification actions remain available to pending users.
2. Use random, hashed, single-use verification links with a 24-hour expiry, resend cooldown and user/IP throttles. A GET never consumes a link. Confirmation does not issue an authentication token or bypass password/2FA. Changing the account email invalidates stale verification proof and pending links.
3. Keep account mail separate from paid manager-message entitlements. Do not print reset/verification/invitation secrets through console mail. Authentication-bound resend errors may be actionable; unauthenticated recovery responses remain generic even if delivery fails. Test with local mail only.
4. Tenant invitations use the manager's scoped tenant record and fixed email. Acceptance verifies access to that mailbox. New accounts choose a validated password; existing accounts must sign in as the invited email and cannot have their password replaced by an invitation. Never attach to a platform/manager account, grant a manager role or silently switch workspaces. Recheck active workspace/tenant, changed email, expiry, revocation and replay under locks.
5. Keep password reset separate from MFA removal. Refuse to overwrite an already confirmed authenticator. Require current password and authenticator code to remove it; rate-limit attempts and audit changes. No new full MFA-recovery system is included in this MVP pass.
6. Persist tour progress per user/workspace and stable tour/step IDs. Steps have a module, role and availability condition. Preserve completed IDs when a newer tour adds steps; offer new guidance rather than forcing a complete restart. Support start, next/back, pause/resume, skip, replay and finish without performing business actions or changing setup completion.
7. Provide only guidance for currently implemented routes. Manager tour: dashboard, properties, tenants, leases, billing and maintenance; Reports is excluded. Future tenant/payments/messaging steps can be registered after those workflows exist and pass role/entitlement checks. Support access must not overwrite a customer's tour progress.

## API integration

All routes below use the existing `/api/v1/` prefix and standard response envelope.

| Route | Purpose |
| --- | --- |
| `GET/POST accounts/email-verification/` | Own verification status or resend; authenticated |
| `POST accounts/email-verification/confirm/` | Explicitly consume a mailbox link; no automatic login |
| `POST accounts/invitations/preview/` | Preview a token-bound tenant invitation |
| `POST accounts/invitations/accept/` | Accept with validated password, or authenticated invited account |
| `POST tenants/{public_id}/invite/` | Manager sends or replaces a scoped invitation |
| `POST tenants/{public_id}/revoke-invite/` | Manager revokes pending invitations |
| `GET/PATCH accounts/guided-tour/` | Own eligible steps, saved progress and navigation actions |

`accounts/me/` includes `email_verification`. A pending new account receives `email_verification_required` on workspace access; account security and verification remain available. The frontend must handle this before redirecting to setup. Two-factor removal now requires `password` and `code`. Tour actions are `start`, `resume`, `next`, `back`, `pause`, `skip`, `finish`, `replay` and `new_steps`. Keep stable step IDs when extending the registry; increment its revision and add matching frontend targets only after their routes are implemented.

## Delivery status — 25 October 2026

Backend and approved frontend implemented locally in focused commits. Existing Business / Property / Unit setup and checklist structure are retained. New account guards route pending users to verification before fetching workspace data. Tenant profiles expose send/resend/revoke controls and a safe invitation status; acceptance supports new accounts and existing accounts returning from password/2FA sign-in. Legacy accounts can request verification from Security without an abrupt access cutoff.

The optional Product tour control is available after manager setup, and for tenant account guidance. Desktop coachmarks anchor to existing controls; phones use a bottom panel. Progress supports next/back, pause/resume, skip, completion, replay and newly registered steps. Stable IDs preserve previous completion history. Account links remove tokens from the visible URL and exclude assistant credentials; invitation continuation is scoped to this deployment's browser session.

No user, test-environment or production database has been migrated. No push or deployment was performed. Account messages were validated with local test mail, not live delivery. Deploy backend and frontend together and verify configured mail delivery in the isolated test environment before releasing registration.

## Validation evidence

Validation completed locally:

- Full backend SQLite suite after the shared access changes: 560 passed, seven PostgreSQL-only skips. A prior full PostgreSQL run passed 565 tests before final access refinements. Its subsequent regression run exposed four unsaved permission-test fixtures; those fixtures were corrected and the complete accounts/platform-permission rerun passed 72 tests.
- After UI integration, all accounts/tenants tests on PostgreSQL passed 92 tests, including concurrent verification, invitation and password-reset consumption. The additional email-length boundary passed separately on PostgreSQL. The final account-link/tour rerun passed 33 tests on PostgreSQL, covering role changes during lock acquisition, email-length limits and replay with completed history.
- Django system check, Ruff and migration drift check passed. Production frontend build passed; the existing large-chunk advisory remains. Twelve Node tests passed, including deployment-specific account-link privacy.
- Playwright checked desktop and 390px/320px flows with controlled API responses: explicit verification and URL cleanup, access gating before setup fetch, failed delivery/retry/throttling, new/existing tenant invitations, invitation reload and password/2FA return, expired links, recovery sent/expired states, two-factor removal validation, optional tour start/next/pause/resume/finish/replay/Escape, horizontal overflow and dark mode. Real API behaviors and concurrency were checked separately by Django tests; browser mocks do not establish live email delivery.

Ignored local evidence: `output/account-access-*.log`, `output/playwright/account-access-*-results.txt`, and `output/playwright/access-*.png`. Figma frames are labelled APPROVED; the review map records local implementation. Static designs describe the accepted layout and flows rather than exact pixel parity for every live data state.

Security references: [OWASP email verification](https://cheatsheetseries.owasp.org/cheatsheets/Email_Validation_and_Verification_Cheat_Sheet.html), [OWASP recovery](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html), [OWASP MFA](https://cheatsheetseries.owasp.org/cheatsheets/Multifactor_Authentication_Cheat_Sheet.html). Framework primitives and the existing response/authentication infrastructure remain the source of truth.

## Authenticator QR refinement — 25 October 2026

The user requested QR-based authenticator setup. The existing Security setup section now renders the server's `otpauth` URI as a local SVG using [qrcode.react](https://github.com/zpao/qrcode.react). No external QR service receives the key. Black modules, a white background and a four-module quiet zone preserve scan contrast across themes. A disclosure provides the account, issuer and copyable manual setup key for same-phone setup. Cancel and successful confirmation clear setup from the screen and reset its mutation data; inactive setup mutations are not retained in the query cache. The existing server-generated secret and six-digit verification remain authoritative.

Figma detail references: [desktop](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=206-449) and [phone fallback](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=206-487). Existing page structure is retained.

Validation: production build and four existing backend authenticator/security tests passed. Playwright decoded the rendered demo QR to the exact provisioning URI and checked cancellation, manual-key copy, incorrect/correct confirmation codes, setup cleanup, absence of secrets in request URLs/local storage and 320px layout. Browser responses were controlled test fixtures, with existing real API behavior checked separately. Production dependency audit reported zero vulnerabilities. Local evidence: `output/authenticator-qr-build.log`, `output/playwright/authenticator-qr-results.txt` and the corresponding desktop/phone screenshots. No push or deployment.
