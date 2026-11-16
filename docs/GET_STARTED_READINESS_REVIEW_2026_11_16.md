# Get Started: account first, portfolio second

Scope: review requested 16 November 2026. The user wants customers to finish their
account and payment setup before adding tenants, including bank/mobile-money
details when available or an explicit cash-only arrangement. They also requested
phone-scannable WhatsApp connection, retaining Open WhatsApp, and removal of Get
Started from the sidebar after completion.

Implemented locally after the user authorized the expanded flow on 16 November.
Business, accepted payment methods, billing/reminders and final review now precede
the portfolio checklist. WhatsApp QR pairing remains optional. Get Started hides
after the full required checklist completes; Settings retains Review setup.
Nothing from this update has been deployed.

## Original findings (before this implementation)

- `/setup` combines business, first property and first unit in one submission.
  Its API requires all three, so an account-only phase needs an API change; simply
  hiding property fields would not work.
- The checklist contains workspace, property/unit, tenant, active lease and first
  invoice. Workspace completion currently means only that an organization exists.
- Setup's business form collects name and optional email/phone, but does not collect
  the business address already used by document rendering.
- Invoice payment instructions and the payout receiving account already have
  separate settings, but neither is represented in the checklist.
- Bank and mobile-money instructions exist. An explicit cash-only setup choice is
  not stored, so absence of bank details cannot safely be interpreted as cash-only.
- WhatsApp is currently an optional block after the portfolio checklist, rather
  than part of account preparation. A connection is not equivalent to notification
  consent or proof that a provider is operational.
- Current row-count completion can include archived records or void invoices.
  Completion should describe usable setup, not the mere existence of a row.

## Stage 1: prepare the account

| Task | Contents | Completion policy |
| --- | --- | --- |
| Your account | Name, verified email, contact details, security guidance | Existing account/verification rules; recommend MFA without changing role requirements |
| Business details | Recognisable business name, document address, contact email/phone, country; confirm currency/time zone | Validate actual saved fields; company registration or tax fields would require separately scoped model/UI work |
| How tenants pay | Bank transfer, mobile money such as Airtel Money, and cash; allow combinations | At least one explicitly chosen arrangement; require complete instructions for each selected bank/mobile arrangement; cash-only needs no fictitious bank details |
| Billing and reminders | Review automatic-invoice preference, lead days and reminder preferences | Persist explicit review; distinguish user preference from platform availability; never generate invoices or send messages merely by reviewing setup |
| Connect WhatsApp | Optional phone-bound connection, separate optional notices consent | QR opens a prefilled connection message; keep Open WhatsApp; manual Send and account-side confirmation remain necessary |
| Review | Business identity, chosen payment arrangements and availability summary | Mark account ready from validated server state, then offer portfolio setup |

Bank details printed on an invoice mean **how tenants pay the workspace directly**.
The receiving account means **where Dwella sends withdrawals**. Never substitute
one for the other or treat a saved payout account as complete invoice instructions.

The online receiving-account task is relevant only when available and wanted.
Platform-disabled collection/payout services must not prevent a legitimate
cash-only/manual-recording workspace from proceeding. Provider credentials and
global activation belong to the platform administrator.

Cash support must preserve financial truth. Website manual cash recording already
exists. WhatsApp currently supports a tenant reporting a cash payment and an
authorized manager confirming receipt; the report alone does not pay an invoice.
Direct manager-initiated “Record cash received” in WhatsApp is an additional
payment-owned capability, not something this checklist can claim to implement.

Rent due day, deposit, late fees and notice period currently belong to each lease.
Reusable workspace defaults and a reusable approved agreement library are useful
future additions, not existing settings to silently invent or mark complete.

## Stage 2: prepare the portfolio

1. Add properties and units, or choose the existing bulk import path.
2. Invite teammates if needed and assign managers to the correct properties.
3. Add/import tenants with the identity, contact and billing facts needed for their
   documents; do not automatically send invitations during a setup review.
4. Create leases, capture existing balances/paid-ahead arrangements where relevant
   and prepare agreements if required.
5. Preview the first invoice, including issuer and payment instructions, then
   explicitly issue/send it and invite the tenant when ready.

Team access is optional for an owner working alone. Property assignment must
precede usable assigned-manager access. Optional channel setup, absent team
members and platform-disabled integrations must not hold overall progress open.

## Completion and navigation

- Hide Get Started from the sidebar when all eight required server checklist
  tasks are complete: business, payment arrangements, billing, account review,
  property/unit, tenant, active lease and first usable invoice.
- Keep “Review setup” available from Settings after sidebar removal. A direct
  `/setup` visit should still work.
- Determine completion server-side for the active account/workspace. Do not store
  an authoritative `done` flag in browser storage or mark tasks complete on click.
- Optional, skipped and platform-unavailable items do not count as missing
  required work. A deliberate cash-only choice is a valid payment arrangement.
- If required saved details are subsequently removed, readiness must reflect it.
- Invited managers see personal setup and their permitted work; business identity,
  payment destinations and workspace-wide choices stay property-admin-only.
- Existing customers keep their records and completed progress. No duplicate
  property, tenant, lease or invoice should be created to complete a new checklist.

## Implementation and validation

`organizations/onboarding.py` retains the original atomic property/unit POST for
older clients. A stage-based POST on the same endpoint now supports `business`,
`payments`, `billing` and `complete`. Account saves require fresh owner or valid
support access, verified access under existing rules, validation, write throttling
and an atomic audit event. New-workspace creation is serialized on the user row;
existing workspaces and portfolio records are reused.

Migration `organizations/0009_account_setup_readiness` stores explicit reviewed
stages, the selected payment methods and final confirmation. Completion also
validates current business data and current active invoice payment instructions;
removing required details reopens setup. An absent bank account is never inferred
to mean cash-only. Selecting cash-only with saved bank/mobile instructions requires
removing those instructions first; they are never silently discarded.

The React account form reuses FormPage, Fluent controls and the existing payment
instruction drawer. Payment-instruction saves/removals refresh readiness. Billing
saves reuse the reminder serializer and preserve scheduler/provider boundaries.
No payout credentials, collection activation or money movement were changed.
The personal profile and security are linked for review; existing mailbox/MFA
access requirements remain authoritative. Invited managers cannot edit workspace
setup and see only their permitted portfolio progress.

Portfolio readiness uses bounded existence checks and excludes archived
properties, inactive records, ended/draft leases, void invoices and opening-balance
invoices. Optional team/WhatsApp setup never blocks completion.

New backend tests cover validation, permissions, verification/suspension,
cross-workspace attempts, malformed input, throttling, audit rollback, current-data
readiness and bounded queries. A measured comparison against the previous service
used seven queries before and after, with both one and 31 properties. This is a
query-count measurement, not a production load claim.

Browser checks use synthetic API responses: business save before portfolio,
bank/Airtel/cash selection, missing-details and billing validation, refresh resume,
Settings review, menu hiding/reappearance and mobile/dark layouts. No live message
or invoice was sent. Production frontend build passes. Full isolated SQLite backend
suite: 1,873 passed, 38 skipped; Ruff and Django checks pass. The test runner uses a
workspace-local temporary folder and development MFA defaults for existing fixtures;
dedicated MFA tests set their own policy. Application/production security settings
are unchanged. PostgreSQL-specific and optional tests remain subject to their own
environment requirements. Browser mocks complement real Django endpoint tests.

Release must include backend migration and frontend together. Existing customers
will review the added account steps without recreating their portfolio. A separate
release and production verification are still required.

Read-only runtime observations were recorded privately in shared memory; no
production configuration, money movement or messaging was changed by this review.
