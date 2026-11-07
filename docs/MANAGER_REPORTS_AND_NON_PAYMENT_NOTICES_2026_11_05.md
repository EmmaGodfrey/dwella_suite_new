# Manager reports and non-payment notices — 5 November 2026

The manager Reports module now includes Collections and Tenant statement alongside
Rent roll and Arrears. The implementation follows the existing report designs
(Figma 275:107 and 275:311) and the approved portal statement hierarchy.
Work is local on develop; the user deferred pushing until after this slice.

## Reports

- Collections shows gross recorded payments, payment counts and a breakdown across
  all six backend payment methods. Reversed payments and void invoices are excluded
  by the existing backend. Pending checkout attempts are not collections.
- Tenant statement requires an explicit tenant selection, including archived
  tenants. It shows opening balance, period charges and payments, closing balance
  and chronological running balances using the existing restated-ledger API.
- Property and tenant selectors search the server and paginate in 25-row pages.
  Tenant selection explicitly switches between active and archived records.
- Date drafts are validated locally (real dates, order, no future end, at most
  366 inclusive days). Applying dates resets report pagination. The backend remains
  authoritative. Method and scope changes reset pagination too.
- CSV uses the applied period and filters, excluding page parameters. Editing a
  date draft does not alter the export or the loaded report.
- Amounts retain decimal strings and use the server currency. Rendering uses
  BigInt for whole units, preserving cents for values beyond Number precision.
- Loading, empty, invalid response, access/error recovery, CSV throttling and page
  boundaries are covered. Narrow layouts show compact activity entries.

API calls live in `frontend/src/Services/activityReports.js`; response decoding and
filter projection live in `shared/activityReports.mjs`. The new screen is
`Components/Reports/ActivityReports.jsx`. `shared/components/AccountStatement.jsx`
shares the approved balances/activity presentation with the tenant portal.
Rent roll and Arrears retain their existing data flow and rendering.

## Non-payment WhatsApp templates

`backend/apps/notifications/non_money_templates.py` supplies fixed body parameters
to the existing operational dispatcher. Parameter order follows the Meta handoff:

| Template | Trigger / recipient | Body parameters |
| --- | --- | --- |
| `dwella_repair_reported` | Repair created / manager | Manager, tenant, repair reference, unit |
| `dwella_repair_update` | Repair status changed / tenant | Tenant, repair reference, unit, current status |
| `dwella_lease_ready` | Lease pending signature / tenant | Tenant, workspace, unit |
| `dwella_connect_whatsapp` | Completed notification-consented connection | Name |

Common-area repairs use “Common areas” when no unit exists. Parameters collapse
whitespace. Repair descriptions, internal comments, access notes and costs are not
added to these templates. Comments and other events do not reuse a status template.

The existing dispatcher uses free text inside the recipient's open 24-hour window;
outside that window it checks approval for the exact template and configured
language. Its existing approved generic operational-template fallback remains.
Missing approval holds delivery. No approval, transport or feature switches were
changed and no real message was sent.

Connection acknowledgements reuse OperationalDelivery, with one identity per
completed NotificationPhoneLink. They are enqueued within the connection
transaction, with a savepoint isolating optional enqueue failure. Dispatch checks
the exact verified/consumed link, current account and workspace membership, current
opt-in and matching verified phone. A newer completed connection suppresses an old
acknowledgement. An actions-only connection does not gain notification consent.
There is no provider call in the HTTP transaction and no schema migration.

Existing allowlists, quiet hours, feature/readiness guards, expiry, deduplication
and conservative unknown-send handling remain in force. Claude's money-template
and payment-proof paths are preserved. PDFs, repair-photo intake and on-demand
WhatsApp reminders are separate remaining work.

## Validation

- Final production frontend build passed; existing large-bundle warning remains.
- All 45 frontend Node tests passed, including filter/CSV projection, envelope
  decoding, exact money and report navigation regressions.
- Production-bundle browser checks with synthetic API fixtures passed seven manager
  groups: populated envelopes/totals, date/export scope, paginated selection,
  archived statements, 390/320px and 200% text/dark layouts, empty/error/retry/
  throttling/pagination, and existing rent-roll/arrears navigation.
- The portal statement browser regression passed all eleven groups after extracting
  the shared presentation, including account choice, credits, running balances,
  loading/access errors, exports, reduced-motion sheet focus and text reflow.
- New non-payment backend tests: 25 passed. Full frozen-source SQLite suite:
  **1,523 passed, 28 PostgreSQL-only skips**. Backend source hashes still match the
  snapshot. Django check, full Ruff and migration drift checks passed.
- PostgreSQL 17 notifications/reports/portal: **442 passed**. Small/full-page
  query budgets remain constant: collections 4, manager statement 6, portal
  statement 8, operational history 4 (JSON and consumed CSV where applicable).
  Disposable PostgreSQL, preview server and browser were stopped after validation.
- Local commits: `2c597e3` shares statement presentation; `3d78ae4` adds manager
  reports; `96a0a3e` wires non-payment notices. Original unrelated billing/views.py
  and portal/tests.py working changes were preserved.

Ignored evidence is in `output/manager-reports/` (snapshot hashes, SQLite/PG logs
and XML, frontend tests and browser scripts/results) and `output/playwright/manager-*`.
Browser layout checks await responsive layout before screenshots; the text-reflow
assertion waits for the compact list to become visible after changing root font size.
No release, deployment, provider activation or push was performed.
