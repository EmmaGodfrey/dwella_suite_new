# Reports refresh

Started 2026-10-28. Scope: improve current rent roll/arrears and add recorded
collections and tenant statements. No payment-processing, provider, pricing or
fund-transfer changes. Frontend implementation follows the saved Figma review
gate; backend report work can proceed independently. No deployment authorized.

## Accuracy contract

- Rent roll and arrears remain current views, not historical snapshots. A unit's
  outstanding balance can include previous tenants; don't attribute it all to
  the currently occupying tenant. Use organization currency and local date.
- Collections use recorded, non-reversed billing payments, excluding void
  invoices, filtered by paid-on date. Pending provider attempts are not income.
  These are gross recorded collections, not provider fees, settlements or net
  withdrawable money. Reading existing payment records stays inside reports;
  the payment implementation remains owned by its existing author.
- Statements use one authorized tenant's currently valid invoices/payments,
  including archived tenants' financial history. Opening balance is charges
  before the selected period less valid payments before it; closing is opening
  plus period charges less period credits. Same-date charges precede receipts,
  with stable primary-key ordering inside each category.
- Statement periods describe the current corrected ledger. Voided invoices and
  reversed payments are excluded even if correction occurred later. This is a
  restated statement, not evidence of what the system showed on a past date.
  Do not invent historical snapshots from fields that do not retain them.
- Amounts use Decimal and exact arithmetic. Selected dates, property, tenant,
  currency and basis accompany totals and exports. Statement running balances
  must match across pages and CSV. No provider calls or report snapshots stored.

## API and efficiency plan

Keep existing rent-roll/arrears URLs and response fields compatible. Add
`collections/` and `tenant-statement/` beneath `/api/v1/reports/`. Use the standard
response renderer and top-level pagination, with rows/totals in response_data.

New period reports accept date_from/date_to, property, page/page_size and CSV
export; collections can also filter tenant/method, and statements require tenant.
Default to the current month through today, maximum 366 selected days and 100
rows/page. Validate UUIDs, range and current workspace access before querying.
Use the existing portfolio permission and explicit tenant/property scoping.

Database aggregates compute summary/opening/counts; related fields are selected
deliberately. Statement activity is a SQL union with stable ordering and sliced
in the database, not two complete Python histories. Compute the page's opening
balance with bounded aggregate queries rather than fetching all preceding rows.
CSV iterates in chunks, maintaining only a row buffer and running balance.
Throttle exports separately. Responses contain no cacheable private reports,
identity numbers, provider evidence, credentials or irrelevant notes.

Measure small/full pages and consume the CSV stream inside query capture. The
old regression captured only response construction, missing streaming queries;
correct that before recording the baseline. Query counts must remain independent
of returned rows, apart from deliberate bounded export chunks. Use representative
EXPLAIN plans before proposing new indexes, caches or dependencies.

## Planned focused commits

1. Baseline/stream-query regression and existing-report response correctness.
2. Collections API, access/validation/financial/query-budget tests.
3. Tenant statement API, exact opening/running totals, CSV and boundary tests.
4. Figma review and measured results. Frontend hooks/screen follow approval.

## Validation

Backend check/Ruff/relevant SQLite and PostgreSQL tests. Cover normal reads,
anonymous/tenant/other-workspace/suspended/revoked access, malformed dates/UUIDs,
archive history, partial/reversed/void records, pagination, same-day ordering,
empty periods, safe CSV cells, export throttling and full-stream query budgets.
No real provider activity or live customer data is needed.

Measurements, final API behavior, any deferred work and Figma review links will
be added here as work completes. Functional tests alone are not a production
capacity benchmark or acceptance sign-off.

## Implemented locally — 29 October 2026

All four report endpoints retain workspace portfolio permissions. JSON uses the
central response envelope and top-level pagination; existing `rows`, `totals`,
`page`, `total_rows` and `total_pages` remain in `response_data`. Reports and CSV
responses send `Cache-Control: private, no-store`. Unknown filters are rejected,
including unsupported historical `as_of` requests on current reports.

`collections/` accepts optional `tenant` and `method`, alongside the shared
property, date and pagination filters. It returns gross recorded amount, payment
count and totals for each existing billing payment method. Payment and invoice
must belong to this workspace and reference the same tenant. CSV includes the
period, currency and collection basis. No provider evidence or calls are used.

`tenant-statement/` requires a workspace tenant UUID; archived tenants are valid.
It returns opening, charges, payments, closing and page-opening balances, with
exact running balances on every row. Charges use invoice issue date, payments use
payment date. Credits can precede invoice issue dates and create negative balances.
Both histories are bounded above by the period end before aggregation. CSV emits
explicit opening/closing rows even for periods with no activity. It includes the
tenant name, period, currency and restated-ledger explanation.

Periods default to workspace-local month start through today. End dates cannot
exceed workspace-local today; ranges are at most 366 inclusive days. Page size is
1–100, default 25. Export ignores page slicing and iterates in 500-row chunks.
Export throttling allows 30 requests/hour per user across all report endpoints,
in addition to existing user throttles. JSON reads remain available after the
export-specific limit. Text cells escape spreadsheet formulas; numeric balance
columns remain numbers, including negative credits.

Rent roll and arrears CSVs now include currency, workspace-local date and basis.
Rent roll explicitly describes outstanding as a unit balance that can include
previous tenants. Existing report fields are preserved; added CSV columns are an
intentional compatibility consideration for spreadsheet consumers.

### Measured resource behaviour

SQLite and PostgreSQL 17 show the following request query counts. The CSV counts
include consuming the entire stream, not just constructing the response.

| Report | Small JSON / CSV | Expanded JSON / CSV |
| --- | --- | --- |
| Rent roll | 7 / 7 | 7 / 7 |
| Arrears | 4 / 4 | 4 / 4 |
| Collections | 4 / 4 | 4 / 4 |
| Tenant statement | 6 / 6 | 6 / 6 |

Existing-report fixtures expand by 12 units/invoices; activity fixtures add 99
payment rows. Explicit 1-row versus 100-row page comparisons remain flat. A
statement page starting after the first entry uses at most two additional prefix
aggregates; it does not fetch the preceding history into Python. Rent-roll CSV
prefetches active leases per 500-unit chunk, so large exports deliberately add
bounded chunk queries rather than one query per returned unit.

A separate fictional PostgreSQL fixture with 1,000 extra payments was inspected
using `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)`. Collections aggregate/page took
4.372/15.586 ms; statement charge aggregate, payment aggregate and 100-row union
page took 0.043/3.179/2.034 ms. These executions wrote no temporary blocks.
This is one local sample, not an SLA or evidence of production capacity. Aggregate
work still grows with matching ledger size; fixed query counts do not imply fixed
database work. No indexes, dependencies, persisted snapshots or caches were added.
Private reproducible fixture and logs are ignored under `output/reports_*` and
`output/reports-*`; they contain fictional data only.

### Figma review — frontend approval pending

Review page: **Reports — Collections & statements · 29 Oct** (`275:106`) in the
existing Dwella Product Design file. New frames preserve the existing Reports
shell and reuse local Buttons, Text Fields, semantic color/spacing variables and
Figtree/Montserrat styles. Ledger rows are reusable local components. Values are
fictional and reconcile within each example.

- [Collections desktop](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=275-107)
- [Tenant statement desktop](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=275-311)
- [Choose tenant](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=275-502)
- [Loading, empty, error and date-validation guidance](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=275-635)
- [Tenant statement mobile](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=275-741)
- [Collections dark](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=275-801)

Desktop collections/statements, mobile and dark composition screenshots were
inspected. Structural checks found no horizontal child overflow and no unexpected
font families. The only image nodes are existing 32×28 logo marks; report UI is
editable text, layout, vector and component instances. State guidance describes
implementation behaviour; it is not an interactive prototype. The existing
rent-roll/arrears designs remain intact. No new frontend implementation or browser
acceptance is claimed. Review these proposals before adding frontend hooks/screens.
