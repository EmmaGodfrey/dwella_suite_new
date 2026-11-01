# Tenant onboarding and combined imports

The first tenant-flow phase adds complete individual/company records and imports units, tenants and draft leases together. It follows the approved 29 October tenant drawer and combined-import designs.

## Tenant details

Managers can save an incomplete record explicitly and return to a missing-details checklist. Name and a valid phone remain necessary to record a tenant. New documents additionally need a ten-digit TPIN and billing address; individuals need an identity document and issuing country, while companies need registration and authorised representative details. TPINs retain leading zeros and are format checked, not verified with a tax authority.

The tenant directory can filter missing details. List responses mask identity numbers; the edit drawer waits for the full detail response. Full values stay within the existing manager/workspace permission boundary. Missing details block direct lease activation and new invoice/agreement PDFs. Payments and repairs remain available. Receipt data reports missing details without reversing or losing payments; previously recorded receipts and saved PDFs remain accessible.

## Combined import

`/tenants/import-template/`, `import-preview/` and `import-confirm/` accept `?kind=tenancies`. Tenant-only and unit-only imports remain available. The UI accepts CSV or XLSX with one worksheet, up to 500 rows and 1 MB.

Unit columns precede tenant columns. Blank tenant/lease columns create vacant units; occupied rows need tenant details and lease dates. Existing units and tenants can be linked after preview, without overwriting their details. Ambiguous property names, conflicting tenant identities, unavailable units, duplicate unit rows and changed records are rejected or marked for review. Incomplete tenants are flagged and can be imported with draft leases.

Confirmation imports the displayed ready subset atomically, with workspace and capacity locks, batch inserts and a one-time audit receipt. It creates no active leases, invoices, payment/deposit entries or invitations. Historical opening balances are a separate reviewed ledger migration; balance columns are explicitly rejected rather than silently discarded.

Import previews use opaque random tokens, compressed and encrypted server-side cache data and a 30-minute expiry; a new preview replaces the previous preview for that actor, workspace and import kind. Tokens contain no readable identity data and are bound to actor, workspace and import kind. XLSX parsing bounds archive expansion and cell counts, rejects formulas, XML entities, macros and external workbook links, and requires text identity/phone cells. Correction CSV downloads neutralise spreadsheet formulas.

Unit floor area is removed from storage, API, forms, tables and templates as previously approved. Its migration intentionally discards those values.

## Validation and release

Regression coverage includes individual/company completeness, partial updates, masking, workspace isolation, incomplete activation/documents, payment preservation, saved-document access, encrypted/replayed/expired previews, import capacity, matching, row changes, throttling and bounded query counts. PostgreSQL CI now runs the full backend suite so imports and leases are included.

Measured SQLite confirmation at 10/500 combined rows: 14 SELECTs in both cases, 6/31 INSERTs, approximately 0.027/0.608 seconds on the development machine. These are local measurements, not a production capacity claim. Desktop/mobile browser checks use synthetic API responses and exercise identity validation, explicit incomplete saving, CSV/XLSX upload, mixed previews, changed-row recovery and company fields.

Server preparation: `THROTTLE_USER_RATE=6000/hour` and one trusted proxy are configured and verified in both environments. Test scheduler jobs include `renewals` and `billing` alongside its previous jobs. Production's scheduled job list is preserved. The new tenant feature still requires a separately authorised test deployment after the develop push.
