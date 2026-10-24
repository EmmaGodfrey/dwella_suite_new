# Dwella product review — 24 October 2026

This is a review of the repository after the approved document/signing work. It records working slices and gaps, not a claim that everything in the original requirements is delivered or deployed. Evidence comes from registered frontend routes, backend models/views/services/commands, tests and operator documents. The current three account types and later approved scope take precedence over the older, broader requirements document.

**MVP scope clarification, 24 October 2026:** The subsequent module-by-module review is complete; [MVP_SCOPE_2026_10_24.md](MVP_SCOPE_2026_10_24.md) records the agreed scope. It includes tenant self-service, bulk unit/tenant imports, lease renewal, Lenco mobile-money/card collection and email/SMS/WhatsApp communications. Reports is excluded from this review. The gaps below remain a product inventory rather than a requirement to build everything. Preserve existing page structures; broader accounting, inspections, subscriptions and other deferred additions remain later scope. The implementation findings below describe what was present at the time of the audit, not completion of the newly agreed work.

The readability/modal improvements were previously pushed to `develop`. This document/signing work is committed locally on `develop`; production and staging were not changed. Launch configuration and live delivery still need environment-specific verification.

## Working product slices

| Area | Implemented in code | Remaining boundary | Evidence |
| --- | --- | --- | --- |
| Account access | Login, recovery, optional TOTP, profile/avatar, identity submission/review, configurable registration | Registration is not proof of email ownership; no general email-verification/invitation acceptance workflow | `backend/apps/accounts/{urls.py,registration.py,views.py}`; `frontend/src/Auth/`, `Components/{Profile,Security}/` |
| Workspace and setup | Business details, first property/unit wizard, persistent setup checklist, scoped manager access | A checklist exists; the guided first-visit tour does not | `backend/apps/organizations/onboarding.py`; `frontend/src/Components/Setup/` |
| Properties and units | Records, photos, unit/rent/vacancy management and scoped filtering | No inspection workflow or owner-statement module; property-level assignment permissions are outside the current two workspace roles | `backend/apps/properties/`; `frontend/src/Components/Properties/` |
| Tenants | Contact/identity records, search, tenancy context and manager forms | A tenant account type exists, but a tenant self-service dashboard, payments/history and repair-submission portal are not delivered | `backend/apps/tenants/`; `frontend/src/Components/Tenants/`; `frontend/src/shared/navigation.jsx` |
| Lease lifecycle | Draft, activate, end, key terms, history and expiry visibility | No dedicated renewal/amendment workflow or deposit settlement/refund ledger; storing deposit terms is not settling a deposit | `backend/apps/leases/`; `frontend/src/Components/Leases/` |
| Billing and receipts | Monthly invoice generation, one-off charges, late fees, partial/full manual payment records, numbered receipts, reasoned reversals, balances | No bank/mobile-money processing, autopay, reconciliation or cross-invoice allocation engine | `backend/apps/billing/`; `frontend/src/Components/Billing/` |
| Documents and lease signing | Branded invoice/lease PDFs, exact saved-PDF previews/downloads, private versions, phone drawing, image/PDF selection, email-verified tenant signing, signing records and original PDF retention | Requires manager-supplied approved agreement wording and configured SMTP; not a general document library or certificate-based signing service | `backend/apps/documents/`; `frontend/src/Components/Documents/`; [workflow notes](DOCUMENTS_AND_SIGNING.md) |
| Maintenance and vendors | Preserved four-lane board/list, requests, photos/comments, vendor assignment, scheduling, costs, completion and optional tenant charge | Tenant self-service submission and broader work-order approval/procurement are not built | `backend/apps/maintenance/`; `frontend/src/Components/Maintenance/` |
| Dashboard and reports | Live portfolio metrics; rent roll and arrears/ageing with property filtering and CSV | No complete historical accounting, income-vs-expense, owner statement or full reporting catalogue | `backend/apps/properties/views.py`; `backend/apps/reports/`; `frontend/src/Components/{Dashboard,Reports}/` |
| Notifications | Scoped in-app overdue/expiry/repair/payment alerts and per-user read state | Alerts are bounded live queries; no general delivered rent-reminder email/SMS/WhatsApp pipeline | `backend/apps/notifications/views.py`; `shared/components/NotificationBell.jsx` |
| Platform administration | Users, identity decisions, workspace lifecycle, explicit timed support access, scoped acting mode, audit browsing/export, platform settings and metrics | This implements the approved console, not subscription billing or an accountant/maintenance/read-only role hierarchy | `backend/apps/audit/`; `frontend/src/Components/Platform/`; [console](ADMIN_CONSOLE.md) |
| Beta onboarding | Signup review, early-access provisioning, configurable transactional welcome/countdown delivery | Live registration/delivery and production backup/restore need launch checks; beta mail is separate from a general communication engine | `backend/apps/marketing/`; `Components/BetaSignups/`; [beta scope](OPEN_BETA.md) |
| Outreach | Contacts/imports, editable templates/sequences, review and approval snapshots, outbox, suppression, early-access handoff | Scheduled sender, send windows/caps, unsubscribe/bounce handling and IMAP replies remain unfinished; sender/provider/offer/cap decisions remain open | `backend/apps/outreach/`; `Components/Outreach/`; [remaining work](OUTREACH.md) |
| Handy assistant | Optional official widget, scoped short-lived access, administrator switch and nine guarded write actions | Depends on an independently configured agent/environment. It does not replace onboarding and is excluded from public signing pages | `backend/apps/assistant/urls.py`; `accounts/handy_agent.py`; `Services/handyAgent.js`; [configuration](PROPERTY_MANAGER_AND_ASSISTANT_SETTINGS.md) |
| Shared presentation | White content surfaces, responsive focused modals/drawers, preserved Maintenance structure, Fluent controls, light/dark themes | Continue task-specific polish as new flows are designed; do not restructure existing pages for visual novelty | [UI review and verification](UI_SURFACES_REVIEW_2026_10_24.md) |

## Not delivered as product modules

- **Expenses and cash-flow accounting:** maintenance cost fields are not an expense ledger, expense approvals or income-versus-expense accounting.
- **Inspections:** `backend/apps/inspections/` contains app/URL scaffolding, without inspection models, workflow, forms or checklists.
- **Owner statements and payouts:** `backend/apps/owners/` is scaffolding; there is no owner reconciliation or statement-generation workflow. This is future scope after the later simplification of account roles.
- **Subscription collection:** a billing-independent access-policy foundation now exists in `backend/apps/subscriptions/`, with optional workspace feature grants/expiry, record limits, scoped APIs and backend guards. Tier names, pricing, billable-unit rules, subscription lifecycle and checkout/collection remain undecided and unimplemented. See [SUBSCRIPTION_READINESS.md](SUBSCRIPTION_READINESS.md).
- **General document management:** invoice/lease records, identity uploads and maintenance photos exist in their own workflows; universal attachments, visibility policies, search and storage abstraction across every entity do not.
- **Guided first-use tour:** no tour, per-user completion/resume state or replay control exists. The current setup checklist should be reused as its foundation.

## External or operational work still required

| Item | Actual state | Next concrete step |
| --- | --- | --- |
| Signing delivery and agreement wording | Code is ready; live SMTP and approved wording were not verified or supplied by this implementation | Confirm the issuer/manager information and actual agreement text, configure delivery, then test with designated internal recipients in staging |
| ZRA Smart Invoice | Models/settings/retry behavior and tests exist, but `FakeVsdcClient` remains the default | Obtain approved VSDC/device details, implement/configure the real client and validate against the relevant environment before claiming fiscal issuance |
| Billing automation | `run_billing` is an idempotent management command; production compose includes a beta-mail loop, with no recurring billing scheduler shown | Decide and configure a monitored scheduler, retries and run visibility; independently design recipient reminders |
| Outreach delivery | Management/review slice exists; outbound engine is unfinished | Resolve the sender/provider, approved offer and daily cap before implementing the remaining planned phases |
| Deployment readiness | Feature checks used isolated data, local file mail and an isolated PostgreSQL cluster | Review staging, apply migrations, confirm email, backups/restore, file/storage growth, monitoring and environment settings before release |

## Proposed next design pass

1. **First-time guided access**, as requested: a short optional manager tour anchored to the existing navigation and setup checklist. Cover first property/unit, tenant, lease, invoice/payment and documents. Offer Skip, Continue later and Replay; retain progress per user/workspace. Keep it helpful for empty and existing portfolios and usable on a phone and keyboard. Design in Figma before coding.
2. **Launch blockers and operational confidence:** confirm approved lease wording and email delivery, test account recovery and signing delivery in staging, decide billing scheduling and verify backup restoration. These need explicit environment work; passing local tests is not proof of production setup.
3. **Next functional scope decision:** choose tenant self-service, lease renewal/deposit settlement, or expenses/reporting based on the beta feedback. These are distinct projects; do not start all three or redesign existing page structures without approval.

## Evidence and limits

The document feature was exercised against a fresh scratch database using the real React/Django flow: agreement preparation, manager signature, tenant verification, uploaded-PDF crop/confirmation, second signature, completed PDF download and preserved original attachment. Desktop, phone, dark theme and short/narrow viewports were checked. Full SQLite and PostgreSQL test runs, the latest document-specific security cases, Django/Ruff/migration checks, focused frontend tests and a production build passed. Details and remaining runtime limits are in [DOCUMENTS_AND_SIGNING.md](DOCUMENTS_AND_SIGNING.md).

This review does not re-test every historical screen in a browser, certify production delivery or complete external integrations. It provides the next drawing-board agenda from verified code rather than treating Figma frames, scaffold folders or historical plans as shipped capabilities.
