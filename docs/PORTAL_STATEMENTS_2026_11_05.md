# Tenant portal statements

Beta scope: let tenants read and export their own recorded account activity.
This slice adds the API; the portal screen follows Figma review. It does not
change invoices, payments, opening-balance entry or manager report permissions.

## Access and API

- `GET /api/v1/portal/statements/` lists currently linked, active tenant records
  in the current workspace as paginated `{id, name}` accounts.
- `GET /api/v1/portal/statements/<tenant-uuid>/` returns that account's statement.
  The UUID must belong to the current portal context. Unknown, other-tenant,
  archived and other-workspace UUIDs return the same 404 after portal admission.
- Both routes use the existing tenant-role, verified-access, active-membership,
  workspace-suspension and tenant-portal feature checks. Having a tenant role
  without a linked tenant record is insufficient. Access is checked each request.
- Statement filters: `date_from`, `date_to`, `page`, `page_size`, `export=csv`.
  The workspace-local current month is the default; periods are at most 366
  inclusive days, no future end date, and page size is 1–100. Unknown filters,
  including alternate tenant/property selectors, are rejected.
- JSON uses the central envelope with top-level pagination. All responses,
  including access and validation errors, use `private, no-store`.
  CSV uses the existing 30/hour per-user export throttle in addition to normal
  request throttles. JSON remains available when the export budget is exhausted.

## Ledger meaning

The portal and manager report share one response builder and the existing
`TenantStatement` calculation. Amounts remain decimal strings. Opening balance
is earlier charges less earlier valid payments; closing balance adds charges
and subtracts payments in the selected period. Same-day charges precede payments
with stable row ordering. Pagination and CSV preserve the same running balances.
Empty periods retain their opening/closing balances. Negative balances are credits.

This is the currently corrected ledger, not a historical snapshot. Void invoices
and reversed payments are excluded using their current status. It is not a
deposit ledger or a view of pending provider payments. No financial rows are
created by reading or exporting a statement.

CSV streams in 500-row chunks, includes opening/closing rows and escapes formula
cells. Only statement fields are returned; identity numbers, provider evidence
and manager notes are not part of this response.

## Validation and next step

Tests cover manager/portal parity, exact balances across pages and CSV, multiple
linked accounts, foreign workspace and neighbour isolation, archived/unlinked
records, permission changes, role/anonymous boundaries, malformed input, rejected
writes, date/page limits, CSV formula safety and export throttling.

Full SQLite suite: 1,459 passed, 28 PostgreSQL-only skips. PostgreSQL 17
portal/reports checks: 102 passed. Django check, Ruff, migration drift and
whitespace checks pass. Validation used a frozen source snapshot and guarded
disposable test settings with faster synthetic-account password hashing;
application password settings are unchanged. The local PostgreSQL instance
was stopped after testing. Evidence is ignored under `output/portal-statements/`.

Measured portal queries are 8 for
a one-row page and 8 for a 100-row page; fully consumed CSV also takes 8 queries
before and after adding 99 activity rows. Manager statement remains 6 queries;
collections remains 4. These are query budgets, not a production capacity claim.

Existing report review frames are on Figma page `275:106`; the desktop manager
statement is `275:311`, mobile is `275:741`. They are reference material for the
tenant portal adaptation, not proof that its UI was approved or implemented.
## Portal design review — 5 November 2026

The tenant adaptation is ready for review on the existing Reports page:

- [Start here](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=297-1052)
- [Desktop](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=297-440)
- [Mobile](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=297-657)
- [Dark](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=297-783)
- [Invalid dates](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=297-845)
- [Account choice](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=297-921)
- [Loading, error, empty and access-changed states](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=297-1014)

Entry is Payments → Statement; Payments remains the highlighted navigation
destination. The sole account is selected automatically. When several linked
records exist, the account choice comes before loading a statement. The sample
uses names plus an ordinal to distinguish matching names, without inventing
home labels the account API does not provide.

The screen shows the applied period, exact opening/charges/payments/closing
figures and paginated activity. CSV is the primary action. Dates are applied
explicitly; invalid periods disable applying/exporting. Empty periods retain
opening/closing balances; failed loads show Retry without fabricated zeros.
Mobile activity stacks each entry with its running balance.

All screens use editable text and component instances, existing Dwella tokens
and Figtree/Montserrat styles. Shared responsive activity-row variants are at
`300:694`. Visual review corrected layout sizing, mobile variant widths,
punctuation and alias-colour fallbacks. Checked content fits the frames without
horizontal or vertical overflow. The only image-filled content is the reused
brand mark; no complete-screen raster is used as the deliverable.

These are static review frames with fictional data. No prototype, frontend
implementation, new API behavior, live data change, deployment or release is
implied. Next: user design review, then frontend query hooks, screen/navigation,
date validation, production build and desktop/mobile flow checks.
