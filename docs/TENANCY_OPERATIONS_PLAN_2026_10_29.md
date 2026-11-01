# Tenant records, deposits, invoices, imports, claims and agreements

Date: 2026-10-29. Status: consolidated delivery plan requested by the user; application implementation has not started.

## Direction and delivery boundary

The user requested a coordinated plan for security deposits, invoices resembling ZRA invoices, bulk property/unit/tenant entry, required tenant identity details, tenant claims against landlords supported by evidence, bank details at the bottom of invoices, and AI-assisted tenancy agreements with an option to upload existing agreements.

**User clarification, 2026-10-29:** make the ordinary Dwella invoice as close to the relevant ZRA invoice format as possible now. Actual Smart Invoice integration comes much later. Certification, fiscal submission, device setup and fiscal automation are outside the near-term phases and must not delay them.

Recommendations below distinguish product policy from verified legal requirements. A local legal/tax review is needed for the specific tenancy and tax rules identified below. This plan does not conclude that every landlord has the same tax position or that every tenant must legally possess a TPIN.

## Verified starting point

Read directly from the current workspace on 2026-10-29; deployed behaviour was not checked.

| Area | Existing foundation | Gap to address |
| --- | --- | --- |
| Tenant records | Full name and normalised phone; optional national ID and ten-digit TPIN | Required identity policy, person/company distinction, consistent manual/import validation and existing-record remediation |
| Deposits | Lease deposit amount; deposit invoice-line kind; deposits excluded from existing fiscal payload | No dedicated deposit custody/balance, allocation, deduction, return and transfer lifecycle in the reviewed models |
| Imports | Unit and tenant CSV template, preview, duplicate detection, one-time confirmation; 500 rows, roughly 1 MB, 30-minute preview | Property import; stricter identity fields; unambiguous links and portfolio onboarding guidance |
| Maintenance | Tenant reports, photos/comments and manager charging tenant for completed repairs | Tenant reimbursement claims, independent approval and settlement evidence |
| Invoices | Server PDF, immutable saved document versions, line totals and payment history | Issuer/customer tax and address snapshots, itemised tax presentation and real bank instructions |
| Agreements | Manager-supplied wording, document versions, signing and retained externally signed originals | Reviewed template library, guided builder, optional AI assistance and unsigned-template import |
| Smart Invoice | Fiscal settings, receipt records and simulated VSDC client; simulator is default | Future certified real integration; existing simulator is not proof of production fiscalisation |

Relevant code: `backend/apps/tenants/{models,serializers}.py`, `backend/apps/imports/{importers,services}.py`, `backend/apps/leases/models.py`, `backend/apps/billing/models.py`, `backend/apps/maintenance/models.py`, `backend/apps/documents/{models,snapshots,rendering,services}.py`, `backend/apps/integrations/{models,smart_invoice}.py`, `backend/apps/integrations/zra/client.py`, `backend/config/settings.py`. Existing contracts: `docs/RENEWALS_IMPORTS_ARCHIVE.md` and `docs/DOCUMENTS_AND_SIGNING.md`.

The reviewed unit importer requires an existing property; tenant imports create applicants rather than leases. Neither import currently provides complete occupied-portfolio migration. The invoice PDF currently asks recipients to obtain payment details from the manager. A renderer hook for issuer TPIN exists, but the reviewed invoice snapshot does not populate it.

## Research and implications

1. **Invoice particulars.** ZRA's VAT guidance describes supplier identity/address/TPIN, customer identity and applicable TPIN, serial number/date, quantity, description, net price, discount, VAT and total. Use these as the information reference for Dwella's ordinary invoice; selecting a similar layout does not make it a compliant fiscal invoice. [ZRA VAT guide, section 6.3](https://www.zra.org.zm/wp-content/uploads/2025/08/VAT-GUIDE.pdf).
2. **Fiscal details are distinct.** ZRA's CIS specification illustrates invoice layout and fiscal information. Its troubleshooting guidance identifies SDC details and fiscal signatures as Smart Invoice features. Keep these absent from ordinary documents. [ZRA CIS specification and sample layouts](https://www.zra.org.zm/wp-content/uploads/2024/04/Smart-Invoice-Specification-of-CIS-for-VSDC.pdf), [ZRA common errors and solutions](https://www.zra.org.zm/wp-content/uploads/2025/06/SMART-INVOICE-COMMON-ERRORS-AND-SOLUTIONS.pdf).
3. **Future integration has prerequisites.** ZRA describes certified systems connecting through VSDC; its FAQ includes Rental Tax among eligible tax registrations. Do not assume Smart Invoice is only relevant to VAT taxpayers. Before future implementation, obtain the then-current specification and confirm applicable obligations/exemptions for each issuer. [ZRA integration guidance](https://www.zra.org.zm/smart-invoice-learn-more/), [ZRA May 2025 FAQ](https://www.zra.org.zm/wp-content/uploads/2025/06/SMART-INVOICE-FAQs-MAY-2025.pdf).
4. **Tenancy rules need jurisdiction-specific treatment.** The Rent Act addresses premiums and possession; section 24 sets a default repair allocation, with fair wear and tear excepted from tenant upkeep obligations. This supports recording condition and repair evidence, but does not establish an automatic right to deduct any repair bill from rent. Have a Zambian practitioner review applicability, deposits/premiums, rent advances, deductions, notices and residential versus business-premises templates. [Rent Act, consolidated text](https://zambialii.org/akn/zm/act/1972/10/eng%402018-04-11), [National Assembly source](https://www.parliament.gov.zm/node/984).
5. **AI and document hosting affect personal-data handling.** The Data Protection Commission's guide addresses local storage and overseas transfers. Review the applicable permissions, hosting, processors and contracts before transmitting lease files to an overseas AI/OCR service; consent alone must not be treated as resolving all requirements. [DPC quick guide](https://www.dataprotection.gov.zm/wp-content/uploads/2025/03/DATA-PROTECTION-QUICK-GUIDE_2.pdf).

Some direct source downloads timed out or were denied; indexed extracts were available. These establish planning direction, not completed legal verification. No universal Zambian deposit cap, mandatory interest scheme or refund deadline was established in this research. Do not import South African/UK deposit rules. Do not hard-code rental-income tax bands from conflicting commercial guides; automated tax returns are outside this work.

## 1. Complete tenant details

**Default proposed policy:** require full legal name, phone number, TPIN and NRC number when saving a new Zambian individual tenant, in both the single-record form and bulk import. This implements the user's requested fields as a Dwella policy; it is not a claim that all these fields are statutory prerequisites for every tenancy.

- Store TPIN/NRC as text; retain leading zeros. Validate ten-digit TPIN syntax without describing it as ZRA-verified.
- Use identity type and issuing country to support a passport or another approved identity document for non-Zambian tenants. Validate NRC format using confirmed rules; do not invent check digits or overly restrictive name rules.
- Add individual/company tenant type. Companies need registered legal name, TPIN, registration details and authorised representative; an NRC is not the company's identity. Keep representative details distinct.
- Email remains optional for recording a tenant, but required and verified through the existing flow before email-based invitation/signing.
- **User-approved policy, 2026-10-29:** allow an explicitly incomplete tenant onboarding record, with missing fields clearly flagged. Required tenant details must be completed before generating an invoice or receipt; enforce this in backend document issuance and show the same checklist in the frontend. A pending TPIN must never be replaced by a dummy value. Recording an actual payment and issuing its document are separate operations: preserve actual payment evidence and allow document generation after completion; do not lose or duplicate a payment because document issuance is blocked. Existing issued documents remain accessible. Final implementation must define the exact completeness checklist for individual/company/foreign-tenant paths.
- Existing tenants stay accessible. Produce a missing-information list and request completion before their next new agreement/document where required, while preserving payments, maintenance and existing agreements. Do not erase history or lock residents out of essential flows.
- Identity duplicates should produce workspace-scoped review warnings. Do not merge people or reject unrelated tenants based only on a shared name, company TPIN or family contact number.
- Mask identity values in lists; limit full values to authorised detail views. Keep NRC off ordinary invoices and notifications. Record why identity data is collected and define retention rules.

Acceptance: the same missing/invalid fields fail through the form, API, CSV and assistant actions; direct activation cannot bypass completeness; existing records remain usable for ongoing obligations.

## 2. Bulk properties, units and tenants

**User clarification, 2026-10-29:** import units and their tenant information together in the same CSV or Excel (XLSX) file, with unit columns first and tenant columns after them. Remove square-metre floor coverage from the database as well as unit forms, API fields, displays and import templates. Remove Unit.floor_area through a migration after checking dependent code; this intentionally discards existing floor-area values. This supersedes the separate-template-only/CSV-first proposal; application implementation is pending.

Extend the existing import workflow and drawer with a combined unit-and-tenant template. Each row identifies the property and unit, followed by tenant identity/contact information; blank tenant columns allow vacant units. Preview the proposed unit-to-tenant links and validate both sections before confirmation. Review existing-unit matches and repeated tenant references rather than silently duplicating or overwriting records. Preserve identity numbers as text in both formats. Imported links must distinguish draft tenancy information from activation, charges and invitations. Separate property and tenant-only templates can remain available.

Recommended sequence: **Properties -> Units -> Tenants -> draft tenancies/opening records**. The first three are immediate scope. Draft tenancy migration and opening balances are a separate increment because importing a tenant alone must not silently create a lease, charge rent or send invitations.

| Template | Required information | Linking and checks |
| --- | --- | --- |
| Properties | Name, property type and address; owner/issuer reference when relevant | Stable property reference; duplicate names/addresses reviewed, never silently combined |
| Units | Property reference, unit label, monthly rent | Match one property within this workspace; reject ambiguous names and duplicate labels in the same property |
| Individual tenants | Full name, phone, TPIN and NRC or approved alternative | Apply the same identity rules as manual entry; show exact row/column errors |
| Companies | Legal name, phone, TPIN, registration and representative details | Separate company identity from representative identity |

Retain template -> preview -> explicit confirm. Show ready, duplicate, invalid and incomplete counts; expose ignored columns. The manager chooses to import the displayed ready subset; confirmation revalidates that exact subset atomically. Invalid rows remain unimported. Export a correction CSV with safe spreadsheet cells. A changed preview, expired token or changed workspace capacity requires another preview.

Keep the current 500-row and approximately 1 MB limits initially. Preserve actor/workspace binding, one-time confirmation, throttling and audit receipts. Do not place national IDs and TPINs in URLs, logs or readable signed client tokens: signing is not encryption. Use a private expiring server-side preview with an opaque token if the preview contains identity data.

Resolve property/unit/tenant links through bounded batch queries; fetch only referenced records. For the existing create loop, measure 10-row and 500-row cases before selecting bulk insert or bounded batches. List/preview reads must not add a lookup query per row. Track inserted rows separately from lookup overhead; record actual timings/query counts during implementation.

Later occupied-portfolio migration must explicitly map tenant to unit/lease dates, distinguish historical balances from new charges, retain opening evidence, and suppress retroactive invoices, reminders and double deposit collection.

## 3. Invoice matching ZRA's information structure now

Use an A4 business invoice inspired by the official samples, with Dwella/issuer branding, restrained typography and a clear totals table. Preserve the existing side-by-side review and exact saved-PDF download workflow.

Proposed document order:

1. **Header:** issuer name/logo; title `INVOICE`; unique invoice reference, issue date, due date and currency.
2. **Issuer:** legal name, address, contacts, TPIN and relevant registration details. Identify a managing agent separately from the landlord when they are different.
3. **Bill to:** tenant legal name, billing address and TPIN; property, unit and lease reference; rental period.
4. **Items:** description, quantity, unit price, discount if supported, tax category/rate, net amount and total. For rent, show the covered period and use one month or another explicit period as the quantity basis.
5. **Totals:** subtotal, discounts, VAT where applicable, invoice total, payments, credits separately, and balance due.
6. **Payment instructions at the bottom:** beneficiary/account name, bank, account number, branch/code where applicable, account currency and invoice payment reference. Add a Dwella payment link only when available through the existing collection flow.
7. **Footer:** issuer contact, page/reference and a concise `Not a ZRA Smart Invoice` statement. For multi-page output, keep the bank block together near the end without overlapping totals; repeat reference/page numbers.

Do not print ZRA branding, `Powered by ZRA Smart Invoice`, fabricated SDC identifiers, fiscal signatures or verification QR codes. An optional future payment QR must be explicitly labelled as a payment link. Do not label an ordinary Dwella invoice `Tax Invoice` as a blanket default or suggest it supports input VAT recovery. A closer format does not replace any applicable issuer obligation to use an approved invoicing channel.

**Issuer decision:** a workspace may manage properties for several owners. Establish who legally supplies the letting before copying the workspace name/TPIN onto every invoice. Recommended model: a billing issuer profile, with a workspace default and property-level assignment where owners differ. This is a small document identity feature, not a complete owner accounting module.

**Tax presentation:** do not automatically add 16% to every rent line. Resolve actual use at unit level for mixed-use properties and distinguish taxable, exempt, zero-rated and unregistered treatment. Rental-income tax is separate from VAT and is not automatically added as a tenant charge. Finance-reviewed issuer/line settings determine treatment. Preserve the agreed inclusive/exclusive basis and exact Decimal rounding; never silently increase an existing lease rent.

**Bank details:** these are invoice payment instructions. A Lenco payout destination is not automatically the account a tenant should pay. Reuse a known account only after its purpose is established. An authorised manager configures instructions once in Settings, selects any property override, and previews them before issue. Validate fields and audit changes; no AI or unauthorised tenant can edit them.

**Snapshots:** freeze issuer/customer details, address, TPIN, tax lines and bank instructions in each issued version. Settings changes apply to new documents, not historical PDFs. Keep the existing version/history model; document reprints must not create duplicate charges. Separate the issued invoice from a current account statement so payment/credit updates do not silently rewrite previously issued content. Correct financial errors through traceable adjustments rather than destroying the original.

Acceptance: saved PDF and preview match; bank details remain visible on long documents; long names and addresses wrap; totals reconcile; NRC is absent; changing bank settings cannot change an old PDF; no simulated fiscal evidence appears. This phase needs no Smart Invoice credentials or device.

## 4. Security deposits

Recommended accounting treatment: record a refundable deposit as money held for the tenant, separate from rent revenue. Track who actually holds it. Dwella recording a deposit does not establish that Dwella or Lenco holds protected or escrow funds.

Add a deposit account linked to the tenant and tenancy, with append-only entries for opening custody, confirmed collection, reversal, approved application, refund and renewal/tenancy transfer. Each monetary posting has a source/reference, actor, date, exact amount, currency and idempotency key. Corrections use reversal entries.

`held balance = verified opening balance + confirmed collections + transfers in - valid applications - completed refunds - transfers out`, including the signed effect of reversal entries. Proposed deductions and pending refunds reserve funds separately; they do not prematurely reduce the settled balance. Concurrent actions cannot allocate more than the unreserved balance. Transfers conserve the total across both accounts.

Flow:

1. Agree the amount and terms in the lease; state permitted deductions and the agreed return process. Do not present an unverified statutory default.
2. Issue a separate deposit request/receipt. If a combined collection is supported, explicitly allocate its rent and deposit portions before posting; a partial payment cannot be treated as fully funding both.
3. Record collection only after confirmation or evidenced manual receipt. Imported opening balances identify the date and custodian and must not create a new cash receipt.
4. Record move-in inventory/photos and tenant acknowledgement. Record move-out condition, meters/keys and dated evidence.
5. Propose itemised deductions with reasons, amount and evidence. Let the tenant accept or dispute; retain the response. Ordinary wear, unsupported damage and unilateral retention must not be automatically posted as settled deductions.
6. Record an approved refund and then its actual completion/reference. Failed or pending transfers remain unpaid. Return any agreed undisputed amount while tracking the unresolved portion separately when appropriate.
7. On renewal, transfer existing custody once and request only a documented top-up. Ending/archiving a tenancy must not erase a deposit obligation.

Example: K5,000 confirmed held, K800 valid deduction and K4,200 completed refund leaves K0 held. Before the refund completes, K4,200 remains a liability even if a manager has approved payment.

The current fiscal code excludes deposit lines; retain this as an existing implementation assumption, not a researched universal tax conclusion. Have a tax practitioner confirm refundable-deposit treatment and what happens when funds are applied to rent, damages or another supply. Applying a deposit to an already invoiced debt must not invoice that debt twice.

Near-term settlement can be manual with evidence. Automated deposit collections/refunds and changes to Lenco payout routing require the established payments-owner workflow and separate implementation; this plan defines the business requirements only.

## 5. Tenant reimbursement claims

Interpretation: the tenant paid an expense they believe the landlord should bear, such as an agreed repair, and asks to be reimbursed. A claim is not automatically a landlord debt or a tax invoice.

Add **Request reimbursement** beside the relevant maintenance request, plus a standalone tenancy claim for an expense not previously logged. Tenant supplies amount/currency, expense date, explanation, supplier/receipt reference, receipt or payment proof, photographs when useful, and prior approval evidence or emergency explanation.

States: draft -> submitted -> under review -> more information / approved / partly approved / rejected / disputed -> settled. Retain who approved the amount, the reason, all evidence and every settlement. Resubmission creates an auditable revision. Submitted evidence cannot be silently replaced. Approval and payment are distinct events.

- Manager checks lease responsibility, actual payment, duplicate claims and prior authorisation. Emergency requests are reviewable; lack of preapproval is not an automatic legal conclusion.
- Notify the tenant of the decision and explain partial approvals/rejections. Allow a response/dispute; Dwella records the case and does not adjudicate legal liability.
- Settle through an evidenced reimbursement first. An agreed rent offset needs explicit agreement, a dedicated ledger allocation and a receipt/reference; never treat it as cash received or silently reduce gross rent for tax purposes.
- A true rent concession and an expense reimbursement are different events. A fiscal credit note, where applicable in the future, must follow the original supply and tax treatment; a reimbursement is not automatically one.
- Link deposit deductions, maintenance charges and claims so the same receipt cannot be billed, deducted and reimbursed twice. Attachment hashes flag possible duplicates for review, not automatic fraud findings.
- Tenant access is limited to their own claims and authorised tenancy evidence. Internal manager notes remain private. Former tenants need a restricted route for outstanding claims/deposit resolution without access to a new occupant's tenancy.

Start with PDF/JPEG/PNG receipts and photos. Use private authenticated storage, file-signature validation, size/page/pixel limits, sanitised previews and metadata stripping. Bound processing time and scans. Reject active or malformed documents; use available malware scanning before exposing originals. Keep evidence retention and deletion rules separate from short-lived processing files.

Acceptance: cross-tenant access denied; unsupported claims cannot post financial entries; partial approval and dispute preserved; replayed approval/settlement cannot double-pay; a K300 claim against K3,000 rent leaves rent due unchanged until a valid settlement/offset is recorded.

## 6. Guided agreements with optional AI

Launch three entry paths in the existing lease preparation view:

| Path | Behaviour |
| --- | --- |
| Build with guidance | Ask plain-language questions and assemble a reviewed template; work without AI |
| Use my agreement | Retain an uploaded signed PDF as an original, or import an unsigned template for review |
| Use a saved template | Reuse a workspace-approved template version with current tenancy facts |

### Builder

Start with a Zambian residential template reviewed by a local practitioner. Keep commercial and unusual tenancies in a separately reviewed path. Questions cover legal parties and agent authority, premises/use, dates, rent/due day, deposit custody/return, utilities, repairs, access, inventory, occupants/subletting, notices, renewal and disputes. Explain each choice and show missing/conflicting answers. Clause options for notices, fees and rent advances need legal review rather than permissive arbitrary defaults.

Read the financial and identity facts from the lease/profile, have the manager confirm them, and insert them deterministically. The agreement and invoice must not disagree on rent, deposit or party identity. Update a draft through an explicit save; never let a model silently change authoritative records.

### AI role and initial technical choice

Use one small instruction-following model through a server-side provider adapter, selected after a short evaluation of available models, cost, output quality and data handling. Do not train a custom model for the first release. No provider/model purchase or integration is selected by this plan.

AI can explain a reviewed clause, suggest wording within permitted sections, summarise imported terms and flag missing/conflicting terms. Feed it the approved clause set and a structured task; require structured output with clause references, assumptions and warnings. Use placeholders for names, addresses, NRC, TPIN and bank accounts and insert real values locally. Redaction reduces exposure but does not itself prove a document is anonymous or legally transferable.

The model cannot invent rent/dates/identity data, decide legal validity, approve a reimbursement, issue/sign a lease, activate a tenancy, or update bank/payment instructions. Uploaded text is untrusted content, including instructions embedded in it. Give the drafting worker no financial tools, unrestricted database access or external URL fetching.

Keep manager approval and signatory authority checks in the existing signing flow. Show exact proposed text changes before acceptance. Store accepted wording and template/prompt/model version metadata with the prepared version; exclude private prompt contents from routine logs. Changed material terms require a new reviewed version and renewed signatures.

### Uploaded agreements

- **Already signed PDF:** preserve the original bytes and label it as uploaded, not Dwella-verified. Extract a proposed summary only with explicit review; do not rewrite it or imply it was signed through Dwella.
- **Unsigned PDF:** extract text and show it beside the source. Flag unreadable pages; require manual entry or bounded OCR with human correction. Never describe extraction as complete when clauses were not read.
- **DOCX support:** a second increment if needed; isolate extraction, reject macros/embedded executables and do not execute external relationships. Do not promise Word layout fidelity in the first release.
- Extracted rent/deposit/dates are suggestions. Manager resolves differences against the recorded tenancy before preparing a new version. Store reusable template wording without a previous tenant's personal details or signatures.

### AI release checks

Evaluate at least 30 representative fictional cases: standard tenancy, missing TPIN/NRC, company/foreign tenant, deposit and utilities, conflicting imported rent, scanned/poor-quality file, hostile document instructions, unsupported fees/notices, provider failure and cross-workspace requests. Require exact preservation of supplied monetary/date facts, no invented identity or authority claims, no tool actions and visible handling of missing information. Legal reviewer evaluates the base clauses and representative generated drafts.

Rate-limit per workspace, cap file/page/context/output size and concurrent jobs, use bounded retries and record per-request cost metadata. Cache reviewed static clause material rather than private tenant documents. Reuse existing job infrastructure; add no GPU service or vector database without measured need. Provider outage must leave manual/template drafting available.

## Delivery phases and reviewable increments

Estimates depend on legal review, approved UI and validation; these are dependencies and release slices, not a promised calendar.

| Phase | Deliverable | Exit condition |
| --- | --- | --- |
| 0 | Confirm individual/company exceptions, actual issuer(s), deposit custody and settlement policy; obtain legal/template review | Documented rules and sample data; unresolved legal/tax items explicitly bounded |
| 1 | Required tenant details and remediation; property CSV import and upgraded tenant templates | Form/API/import parity; clear existing-record handling; idempotent scoped imports |
| 2 | Ordinary invoice layout, issuer profile, tax presentation where applicable, bank instructions and snapshots | Reviewed sample PDFs; historical stability; no fiscal representations; no Smart Invoice dependency |
| 3 | Deposit account, move-in/out evidence, deductions, manual return/renewal handling | Exact balances and concurrency tests; tenant statement; no duplicated rent/deposit posting |
| 4 | Evidence-backed tenant claims, manager review, manual settlement and explicit offsets | Access controls, disputes, partial approvals and replay-safe settlement verified |
| 5 | Guided reviewed agreements and upload-existing path, followed by optional AI assistance | Existing signing integrity preserved; legal review and factual/privacy evaluation passed |
| Much later | Smart Invoice certification and production integration | Separate project using then-current ZRA requirements, real sandbox/live approval and verified receipts |

Within each phase, use focused commits: model/migration and constraints; domain services/validation with tests; scoped API and permission tests; frontend services/hooks; form/document interactions; operational documentation. Use bracketed tags such as `[FEATURE]`, `[BUG FIX]` and `[DOCS]`. Do not bundle unrelated modules into one phase-wide commit.

Frontend work must first read the relevant project UI skills, reuse template components and existing drawers/side-by-side documents, and follow `docs/FRONTEND_DATA_FLOW.md`. Preserve the established design review workflow. This planning task does not request new Figma files or application edits.

## Validation and operational requirements

- Follow plan -> implement -> validate for identity, evidence, money and signing changes. In-place model switching is not exposed in this runtime; no model switch is claimed. Respect the existing payments-owner boundary for actual payment implementation.
- Backend checks: `python manage.py check`, `ruff check .`, relevant pytest tests, migration consistency, then the full backend suite for changes to shared tenant/lease/billing/document behaviour. Include PostgreSQL concurrency checks for deposit allocations, confirmations, approvals and settlements.
- Cover unauthenticated/forbidden/cross-workspace access, archived/former tenant cases, invalid/missing input, replay, stale previews, malformed uploads, throttling, expired links and signing-version changes.
- Frontend production build and touched-flow sanity checks; browser validation where it materially improves confidence for PDF overflow, required forms, imports, evidence access and agreement review.
- Measure preview/import and list paths using small/full workloads. Lists must not issue per-row ORM reads. Track evidence storage, AI usage, task deadlines and operational logs; do not scan full document histories to build summaries.
- Define a legal retention schedule for financial/signed evidence, access restrictions and backups; expire temporary import/OCR/AI work separately. Never place identity files, bank data or signing secrets in public media or logs.
- Add migrations and feature gates in stages; keep existing payments/signatures operational. Pilot on fictional then authorised test data. Do not push, deploy, send messages or move money as part of this plan.

## Outstanding decisions and external verification

Recommended defaults allow design/planning to continue without blocking on a questionnaire:

1. Required full name/TPIN/NRC for new Zambian individual tenants; explicit person/company/foreign-identity paths rather than fake values.
2. Reimbursement claims with manager review; no unilateral rent deduction. Direct evidenced reimbursement is the initial settlement method.
3. Workspace billing default with property-specific issuer/payment instructions where needed; settle the legal issuer before final invoice design.
4. Separate refundable deposit records and evidenced manual returns first; no assumption of escrow, automated refunds or a universal statutory deadline.
5. Reviewed guided residential template first; uploaded signed PDF retained unchanged; unsigned PDF extraction and AI assistance introduced after review.
6. Ordinary invoice resembling ZRA information/layout now; actual Smart Invoice remains far-future scope. Confirm applicable tax-invoice obligations separately so the UI does not imply this deferral changes law.

Before production release, a local practitioner/tax adviser must resolve the affected deposit/premium/advance rules, deduction/refund wording, approved contract clauses, issuer/agent arrangement, tax categories and document retention. Confirm AI/OCR hosting and transfer requirements with appropriate advice before any real tenant documents leave the approved environment.

## Additional product polish discussed, 2026-10-29

User requests more polished invoice/receipt references and replacement of editable status dropdowns. Number format and control designs remain proposals pending review. Suggested visible references: document prefix, year and readable generated code, with database uniqueness and collision retries, immutable after issue and existing references preserved. Review issuer numbering requirements before choosing random rather than sequential document numbering. Status inputs with a few independent choices should use labelled radio groups/segmented controls; workflow states should come from authorised actions and business events. Separate unit occupancy from availability/maintenance so an occupied unit can still need repairs. Consider deriving occupied state from an active tenancy, archiving through a deliberate action and keeping status filters compact. Suggested additional improvements: tenant completeness checklist, unified tenancy history, clear cash-versus-offset allocations and recoverable import previews. User subsequently requested delivery planning for these suggestions. The implementation plan below incorporates them; no application changes or numbering migration have been performed.


## Consolidated delivery plan - 2026-10-29

This section supersedes the earlier delivery-phase table where they differ. The user accepted the additional product suggestions and requested plans. This is a reviewable implementation backlog, not a claim of implementation, a release request or approval of legal/tax rules.

### Agreed product behavior

- Save incomplete tenant onboarding records with a clear missing-details checklist. Complete required identity/billing details before generating invoices or receipts. Preserve actual payment recording separately, and retain access to previously issued documents.
- Collect legal name, phone, tenant type, address, TPIN and the appropriate individual/company identity details. Email is optional until an email-dependent action. Emergency contact is optional and never blocks invoice/receipt issuance. Company and foreign-tenant paths must use appropriate alternatives rather than fake NRC values. Tenant completeness describes data presence/validation, not verified legal identity.
- Import units and tenants together from CSV or XLSX; unit columns first, tenant columns second. Support vacant units without tenant details. Show intended relationships and exact errors before confirmation.
- Remove Unit.floor_area from the database, API, forms, tables and templates. Inventory dependencies before migration; explicitly document that existing values are discarded.
- Improve both invoices and receipts, and introduce more polished references for new documents. Preserve old references and issued versions.
- Replace status-edit dropdowns with visible choices or workflow actions. Keep table filters suited to filtering. Separate occupancy from operational availability/maintenance.
- Track refundable deposits, reimbursement claims, payment allocations and a unified tenancy history. Initial refunds and reimbursement settlements are evidenced manual records; automated money movement is outside this increment.

### Delivery order and acceptance

| Phase | Work | Reviewable acceptance |
| --- | --- | --- |
| 1 - Design and transition rules | Inventory status controls, document generation entry points, reference dependencies and floor-area usages. Design tenant checklist, combined import, status choices, invoice/receipt, deposit and claim surfaces in existing Figma file. Use drawers and side-by-side document previews. | Review desktop/mobile and light/dark examples, empty/error/incomplete states, and the status transition matrix before frontend implementation. Resolve issuer, numbering and settlement rules relevant to each phase. |
| 2 - Tenant foundation and unit simplification | Add tenant-type identity/billing completeness and server-side issuance checks; frontend checklist and completion flow. Remove floor-area dependencies and then its column. | Manual entry, API and assistant actions share validation. Incomplete tenant can be saved; invoice/receipt issuance is blocked with actionable missing fields. Actual payment evidence and historical PDFs remain accessible. Migration and rollback limitations documented. |
| 3 - Combined portfolio import | Extend existing importer with CSV/XLSX parsing, combined unit/tenant rows, safe text identifiers, batched matching, preview and one-time confirmation. Retain standalone routes. | Vacant/occupied rows, repeated tenant references, existing units, invalid identifiers, stale previews and retries are handled explicitly. No silent overwrite, activation, retroactive charge or invitation. Correction export contains failed rows and safe spreadsheet cells. |
| 4 - Documents and references | Issuer profiles and property overrides, invoice bank instructions, revised invoice and receipt layouts, immutable snapshots and new-reference generation. | Preview equals saved PDF; long/multipage documents remain readable. Existing documents retain references/details. Concurrent issuance and retries cannot duplicate documents or payments. Missing tenant details consistently block every issuance route. |
| 5 - Status behavior | Apply approved status controls and transitions across properties, units, tenants, leases, invoices, maintenance and claims, respecting each domain's rules. | Simple choices use accessible radios/segmented controls; financial/workflow states follow valid actions. Archiving is deliberate. An occupied unit can have repairs. Reconcile legacy manual occupancy/reservation data before deriving occupancy; never silently vacate a unit. |
| 6 - Deposits and allocation | Deposit custody ledger, verified opening balances, explicit rent/deposit allocation, deductions/disputes, manual refunds and renewal transfers. | Exact balance reconciliation; pending refunds remain liabilities, proposals reserve separately, duplicate/concurrent actions cannot spend the same balance, and renewal does not recollect existing funds. Evidence and history remain after tenancy ends. |
| 7 - Tenant reimbursements | Maintenance-linked or standalone claims, private evidence, information requests, partial approvals/rejections/disputes and evidenced settlements. | Approval does not imply payment. Agreed rent offsets use explicit allocation without fabricated cash receipts. Partial/multiple settlements cannot exceed approved amounts. Detect potential duplicate evidence for review. |
| 8 - Unified history and agreements | Combine tenancy events into a paginated timeline, then guided reviewed agreement templates, preserved signed uploads and optional AI assistance. | Tenant sees only authorised events; internal notes and full identity values remain restricted. History links to original records/documents. Agreement facts match authoritative tenancy data; AI cannot issue, sign, approve or move money. |

Keep the timeline framework small and introduce events alongside phases 2-7; phase 8 completes the combined view rather than delaying useful history until the end.

### Document and reference specifications

**Invoice:** issuer/agent identity, tenant legal name/billing address/TPIN, property/unit/lease, reference and dates, rental period, itemised charges and applicable tax, totals, bank instructions and available payment link. NRC/passport/emergency contacts are excluded.

**Receipt:** issuer, unique receipt reference, payment date and recorded date where different, payer/tenant, property/unit, exact amount/currency, method and payment reference, allocation across invoices/rent/deposit, relevant covered period and balance as at issuance. Clearly label reversals and preserve the original. A deposit opening balance or noncash offset must not produce a receipt claiming new cash was received. Current balances belong in a separately labelled live summary rather than rewriting issued evidence.

Proposed references: `INV-2026-7K9P4X8M` and `RCT-2026-3H6W9N2R`. Confirm random-versus-sequential issuer requirements before finalising. Use readable uppercase symbols, server generation, database uniqueness, bounded collision retries and issuance idempotency. Scope uniqueness consistently to the document issuer/workspace. Derive the year from the defined issue date/timezone; never renumber historical documents. References are identifiers, not access credentials. Check field lengths, search, exports, PDFs, integrations and assistant responses.

Completeness checks occur before new issuance or automated document jobs. Scheduled issuance must leave a visible actionable blocked state rather than repeatedly failing or silently skipping a tenant. Existing tenant remediation and live payment/receipt coupling need an explicit migration path: payment confirmation remains durable even when document issuance awaits completion. A later retry must generate only the missing document. Establish billing address separately from current address with an explicit reuse option.

### Financial workflow acceptance examples

- K6,000 payment allocated K3,000 rent / K3,000 deposit produces exactly those postings once; a smaller payment requires a deliberate allocation.
- K3,000 held, K400 agreed valid deduction, K2,600 pending refund: K2,600 remains owed until completion; completed refund leaves zero.
- Existing K3,000 deposit imported with custodian/date/evidence creates an opening record, no new collection or cash receipt.
- K800 reimbursement claimed, K600 approved, K200 rejected with reason: settlement is limited to K600, with the decision and tenant response retained.
- K600 agreed offset against K3,000 rent leaves K2,400 payable through a traceable noncash allocation; gross rent and cash records remain explicit.

### Implementation, ownership and release checks

Use focused bracket-tagged commits within each phase: schema/constraints, domain behavior with tests, scoped API, frontend services/hooks, reviewed UI and operational notes. Do not mix unrelated pricing/report work into these commits. Follow plan ? implement ? validate for identity, evidence and financial behavior. This runtime has no in-place model switching; none is claimed. Existing Claude ownership covers payment/Lenco/withdrawal/fee/payout changes; coordinate those interfaces without expanding into automated transfers here.

Run Django check, Ruff, relevant pytest and migration consistency checks; run the full backend suite for final shared changes. Test unauthenticated, forbidden and cross-workspace access, malformed uploads, stale previews, throttling, replay and PostgreSQL financial concurrency. Measure 10/500-row import previews and small/full list pages; bound XLSX expanded size, sheet count and processing time, reject unsupported/encrypted files and do not execute formulas/macros. Retain existing row limits and define file limits from representative XLSX fixtures.

Run frontend production build and touched-flow sanity checks, including keyboard choices, mobile layouts, PDF overflow and failed-save recovery. Pilot with fictional data and reconcile opening balances before any authorised real-data rollout. No push, deployment or real messages/transfers are part of this planning task.

Next deliverable: phase 1 inventory, status transition matrix and Figma review set, followed by the tenant-foundation implementation after design review. Legal/tax review gates apply to affected document/contract rules, not unrelated unit cleanup or import UI design.
