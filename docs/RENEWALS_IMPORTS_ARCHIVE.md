# Lease renewal, bulk imports and tenant archive

Backend for the remaining "Properties and units", "Tenants" and "Leases" rows of [MVP_SCOPE_2026_10_24.md](MVP_SCOPE_2026_10_24.md). The screens follow the approved Figma frames (file aHlQPzHBsvGR4rNoabRQyW, page "Tenant portal, renewal & imports — MVP"): Renew lease on the lease page (`Leases/RenewLeaseDrawer.jsx`), Import CSV on Tenants and Import units on Properties (`Imports/ImportDrawer.jsx`), and archive, restore and remove portal access on the tenant profile (`Tenants/TenantConfirm.jsx`).

## Renew lease

`POST /api/v1/leases/<id>/renew/` with `end_date` and any changed terms (`monthly_rent`, `deposit_amount`, `rent_due_day`, `late_fee_percent`, `late_fee_grace_days`, `notice_period_months`, `notes`). It returns a new draft lease (201).

- **Copied:** the same tenant and unit. Any term the manager doesn't change carries over.
- **Start date:** fixed to the day after the current lease ends. It and the tenant/unit cannot be edited on the draft.
- **Only from an active lease:** a lease can have one open renewal at a time.
- **Lease responses:** these now include `renewal_of_id`, `renewal_of_reference` and `renewal` (the open renewal, if any).
- **Signing:** the renewal is a normal lease, so it is prepared and signed with the existing document flow.
- **Starting the renewal:** this ends the lease it follows with no vacancy.
  - Manual activation is refused before the start date.
  - The `renewals` scheduler job (daily 05:30, before billing) starts due renewals automatically when they have a fully signed version or a retained signed original.
  - Enable the job with `APP_SCHEDULER_JOBS=...,renewals`.
- **Alerts:** an unsigned renewal that is due raises an alert. A lease with a renewal in progress no longer raises an "ends soon" alert.
- **Billing:** a handover month already billed on the earlier lease is not billed again on the renewal.
- **Database rules:**
  - A unit has at most one active lease.
  - It has at most one open non-renewal lease.
  - Each lease has at most one open renewal.
  - New leases lock the unit before their final check.

## Bulk unit and tenant import

Both use the same three calls, on `/api/v1/properties/units/` and `/api/v1/tenants/`:

| Call | Purpose |
| --- | --- |
| `GET import-template/` | CSV with the columns and one example row |
| `POST import-preview/` `{"csv": "<file text>"}` | Every row marked `ready`, `duplicate` (same as an earlier row, or already on file) or `invalid` with field errors; counts, ignored columns and a `preview_token` when anything is ready |
| `POST import-confirm/` `{"preview_token": ...}` | Creates the ready rows (201, `created`, `ids`) |

**Unit columns:**
- Required: `property`, `unit`, `rent_amount`.
- Optional: `bedrooms`, `bathrooms`, `notes`. Unit floor area was removed on 2 November 2026.
- The property must already exist; its name matches ignoring case.
- Rent accepts "K 3,500" style amounts.
- Units start vacant.

**Tenant columns:**
- Required: `full_name`, `phone_number`.
- Optional: `email`, `national_id`, `tpin`, `notes`, `tenant_type`, `identity_type`, `identity_country`, `billing_address`, `company_registration`, `representative_name`, `representative_phone`.
- Phones are normalised, and phone duplicates include archived tenants.
- Tenants start as applicants.

**Header matching:** headers match ignoring case, spaces and hyphens. Common aliases also work (`Name`, `Phone`, `NRC`, `Rent`, `Property Name`).

**Limits:** at most 500 rows and 1 MB per file. A preview lasts 30 minutes and belongs to the manager and workspace that made it. Previews and confirmations are limited to 30 an hour.

**Confirming:**
- It re-checks every row under the workspace's record-limit lock and creates all of them or none. If anything changed, it returns the changed rows and asks for a new upload.
- Each preview can be confirmed once. `PortfolioImport` keeps the receipt, and an audit event records the count.

### Combined portfolio import (2 November 2026)

Add `?kind=tenancies` to the tenant template, preview and confirmation URLs to create units, tenants and **draft** leases together. Upload a CSV/XLSX as multipart `file`, or send CSV text in `csv`. Properties must already exist. A row without tenant or lease fields creates a vacant unit. Occupied rows need tenant name/phone and lease start/end dates; monthly rent defaults to the unit rent. Existing units and tenants are linked only when the reviewed match remains unambiguous; their stored details are not overwritten.

The preview shows the matched property/unit/tenant, row errors and missing document details. Confirmation checks the matches again under the workspace lock, checks capacity for each resource, then writes in bounded batches. Any changed match or conflict requires another preview. It does not activate leases, issue invoices, send invitations or record money. Historical `opening_balance`, `balance`, `arrears` and `deposit_held` columns are rejected: opening financial records remain a separate reviewed migration.

Preview rows are encrypted in the shared cache, bound to the requesting user/workspace and expire after 30 minutes. Only one current preview per user/workspace/import kind is retained; a newer preview invalidates the older one. Tokens contain no tenant data. Successful confirmation records a durable one-use import receipt. Keep the normal shared cache available across web workers.

XLSX accepts one worksheet, at most 60 columns and 500 data rows. Phone and identity cells must be stored as Text to retain leading zeros. Formulas, macros, external links, unsupported XML declarations, oversized archives/XML and malformed text are rejected. These constraints apply before database lookups where possible.

### Tenant details and document preparation

Tenant lists mask identity numbers and TPINs; the authorised detail drawer supports individual/company details and a missing-information checklist. Dwella requires legal name, phone, billing address and TPIN, plus individual identity details or company registration/representative details, before activating a new lease or preparing new tenancy documents. This is product completeness, not verification by an identity or tax authority. Incomplete records remain available for payments, repairs and retained documents. Receipt preparation reports missing details for newer payments without preventing payment recording; previously recorded receipts remain available.

Import regression coverage includes role/workspace boundaries, expiry/replay, throttling, malformed files, changed matches, rollback, capacity and query budgets. Combined confirmation measured 14 SELECTs for both 10 and 500 rows on SQLite; batched INSERTs were 6 and 31 respectively (0.027s and 0.608s in the original local run). These measurements are a local import budget, not a server-capacity claim.

## Archive tenants

`POST /api/v1/tenants/<id>/archive/` and `.../restore/`.

- **Refused while a lease is open:** archiving is refused while the tenant has a draft, awaiting-signature or active lease.
- **Records:** every lease, invoice, payment, document and repair is kept.
- **Access:** pending portal invitations are withdrawn, and the tenant portal closes.
- **Lists:** the tenant list hides archived tenants unless `is_active` is given; `?is_active=false` lists them. Detail pages still open.
- **New leases:** archived tenants cannot be put on a new lease until restored.
- **Audit:** both actions are audited.

Tests: `backend/apps/leases/test_renewals.py`, `backend/apps/imports/tests.py`, and the archive test in `backend/apps/tenants/tests.py`. These were run on SQLite and on PostgreSQL 17.
