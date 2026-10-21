# Landlord open beta — 18 November 2026

Scope agreed 22 October 2026: complete the landlord workflow before tenant access or
external integrations. Work on develop; do not deploy or push without instruction.

## Acceptance checks

1. Billing: record partial/full payments, find and print a numbered receipt, and
   reverse an erroneous payment with a required reason without deleting history.
   Dashboard totals, invoice balances and reports must agree after reversal.
2. Onboarding: create a landlord account when registration is enabled, create a
   workspace and first property/unit, then follow a persistent setup checklist to
   add tenants, activate leases and generate invoices. Existing portfolios bypass
   the first-property wizard. No payout account or delivery integration required.
3. Reports: live rent roll and arrears with property filters, accurate totals,
   ageing bands, links to source records and CSV export.
4. Notifications: a working bell showing overdue invoices, expiring leases and
   open repairs and recent payments, scoped to the active portfolio with personal
   read state. Resolved alerts disappear; read state belongs to each user.

## Security and validation

Use existing DRF permissions, scoped querysets, password validation and throttles.
Public registration cannot grant staff/admin access or select another workspace.
Wizard writes are atomic and restricted to workspace owners/admins. Reports,
receipts and notifications never expose another portfolio to a landlord or tenant.
Financial corrections lock the invoice and preserve receipt/reversal history.
Only workspace owners/admins can edit the business details used as the receipt
issuer, including when they also have a viewer membership in another workspace.
Business dates use Africa/Lusaka; timezone-aware timestamps still use UTC storage.
Test these happy paths and failures, run the full backend suite, Django checks,
Ruff, migration consistency, the frontend production build and browser smoke flows.

## Deferred deliberately

Tenant portal and invites; email/SMS/WhatsApp/mobile-money/ZRA UI integrations;
credit notes, refunds and multi-invoice allocation; lease renewal/deposit settlement;
expenses, documents, team administration and full audit UI. A payment reversal is
a correction to a record, not a refund or a reversal of a bank/mobile transaction.

## Launch configuration

Set `APP_BETA_REGISTRATION_OPEN=true` in the deployment environment when ready to
accept self-service accounts. It defaults to false. Existing users can still sign
in and complete setup. Registration does not mark an email address as verified.
Production email delivery and account recovery must be checked before opening.

## Review locally

- Sign in with your usual development account. Billing → Receipts opens payment
  history; recording a payment opens its new receipt. Print / Save PDF uses the
  browser print dialog. The print document excludes the app shell and internal notes.
- Get started opens the setup wizard for an empty owner workspace, or a checklist
  for an existing portfolio. Draft form values survive refresh in the same browser
  tab and are removed after successful setup. Existing records are not reseeded.
- Reports offers rent roll and arrears, property selection and a full filtered CSV
  export. Totals cover the whole selection rather than just the current page.
  These are current reports, not historical accounting snapshots. Rent-roll unit
  balances include unpaid invoices for previous tenants; arrears identifies each
  owing tenant and source invoice. Unlinked one-off invoices appear in all-property
  arrears as Unassigned, and are excluded from individual-property filters.
- The bell refreshes every minute and after relevant writes. Each source is bounded
  to 100 current alerts; Billing, Leases and Maintenance contain all underlying records.
- SQLite migration backups and synthetic browser screenshots/PDFs are under ignored
  `output/beta-work/`. Never add databases, preview account data or that directory to Git.
- On Windows, if the sandbox prevents Vite's bundled config loader from reading
  parent directories, use `npm run build -- --configLoader native` or
  `npm run dev -- --configLoader native`. The ordinary scripts remain available.

Deployment, opening registration and production delivery checks remain separate
launch actions. Nothing here authorizes pushing to main or deploying.

## Validation on 22 October 2026

- Full backend suite: 223 passed. Includes permissions, cross-workspace access,
  signup throttling and validation, atomic setup, reversals, ageing boundaries,
  CSV formula escaping, receipt identity for backdated payments and Zambia dates
  immediately before UTC midnight.
- `manage.py check`, Ruff and `makemigrations --check --dry-run`: passed.
- Frontend production build: passed with `--configLoader native`.
- Synthetic browser checks: signup → setup → checklist → dashboard; receipt
  history/detail; record payment → the correct receipt; correction/reversal;
  rent roll/arrears and full CSV downloads; notification bell and mark-all-read;
  desktop/mobile layouts; light/dark themes. No browser JavaScript errors.
- Printed receipts: one A4 page from both themes, without app navigation or internal
  notes. Preview PDFs and screenshots are under `output/beta-work/`.
- Existing non-failing warnings remain: backend staticfiles directory/DRF format
  converter and maintenance pagination warnings; Vite's large bundle advisory.
- Google Fonts remain configured as in the existing app. The sandboxed browser
  could not load the external font stylesheet, so its screenshots use the sans-serif
  fallback. Confirm production font delivery during the launch review.
- Local development SQLite was backed up before applying pending migrations;
  the user's existing portfolio data was not seeded or replaced.
