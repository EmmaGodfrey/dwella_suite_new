# Assigned property managers on WhatsApp

An assigned Property Manager could prove their phone number but could not finish
pairing: WhatsApp accepted only `landlord` (Property Admin) and `tenant` memberships,
then returned “This account is not linked to a tenancy.” Managers do not need a
tenant record.

The correction admits active, verified managers and uses the website's existing
property-assignment and temporary-cover scope. Workspace choice, balances,
invoice/receipt/repair lists, detail lookups and requested invoice/receipt PDFs
retain fresh authorization. A manager with no assignments may connect but sees no
property records, with guidance to ask the property admin for assignments in Team.

Scope is reused within one actor context, never across worker dispatches. The
transport reconstructs the context before sending, and after PDF upload, so
assignment removal, cover expiry, membership removal or role changes can cancel
queued replies. Cross-workspace access and unassigned targets remain unavailable.
Property admins retain their workspace-wide access; tenants retain their own
tenancy checks. Consent, exact-phone verification, expiry, single use and rate
limits are unchanged.

Manager menus offer assigned-property reads and the existing website shortcut for
invoice creation. Payment actions and reminders use their existing website flows;
this change does not enable the owner/tenant WhatsApp financial adapters for the
new role or change payment verification, ledger entries or payout permissions.

Validation includes the actual staged pairing endpoint, no-tenancy/no-assignment
cases, assigned and unassigned records/PDFs, cross-workspace refusal, role and
membership revocation, cover expiry, stale buttons and queued replies, and
assignment removal during a mocked private PDF upload. Invoice-list query count
stays flat and bounded at four queries or fewer for one versus 21 invoices.
Focused WhatsApp regression: 104 passed, 3 skipped. Full local and PostgreSQL CI
must pass before deployment.

After release, start a fresh QR connection if the previous ten-minute code has
expired. The user sends the new prefilled message and completes pairing normally;
operators must not bypass phone proof or change the manager into a Property Admin.
