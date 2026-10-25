# Tenant portal API

Backend for the agreed MVP "Tenants and self-service" row ([MVP_SCOPE_2026_10_24.md](MVP_SCOPE_2026_10_24.md)). The tenant screens follow the approved Figma frames (file aHlQPzHBsvGR4rNoabRQyW, page "Tenant portal, renewal & imports — MVP") and live in `frontend/src/Components/Portal/`. Tenants reach them through the usual `/dashboard`, `/leases`, `/billing` and `/maintenance` routes, which render the portal for the tenant persona (`Route/ForTenant.jsx`); API calls sit in `Services/portal.js`.

Known gap: removing portal access deletes the tenant membership, so that account becomes "unassigned" and is sent to workspace Setup like a new property manager sign-up.

## Who gets in

A request reaches `/api/v1/portal/` only when all of these hold (`apps/portal/access.py`):

- the account is not staff/superuser, has passed mailbox proof where required, and its workspace is active;
- its workspace membership has the `tenant` role;
- the workspace has the `tenant_portal` feature;
- at least one active `Tenant` record in that workspace has `user` set to the account. This link is created only by accepting a manager's invitation.

Otherwise the API returns 403; an unlinked tenant gets code `tenancy_not_linked`. Archiving the tenant record or suspending the workspace closes the portal immediately. Managers can call `POST /api/v1/tenants/<id>/remove-portal-access/`: it unlinks the account, withdraws pending invitations and removes the tenant membership (if no other record links the account) so a fresh invitation works later. Records are kept; administrator deactivations are not undone.

## Endpoints

| Method and path | Returns |
| --- | --- |
| `GET overview/` | Balance and overdue balance (strings), next unpaid invoice, current leases, lease documents awaiting the tenant's signature, open repair count, last three payments, manager contact details |
| `GET/PATCH profile/` | Name, phone, email, status. Only the phone number can be changed (normalised, unique per workspace, audited). Email is the signing address and stays manager-controlled |
| `GET leases/`, `leases/<id>/` | Pending-signature, active and ended leases. Drafts are hidden |
| `GET leases/<id>/documents/` | Lease versions that are awaiting signatures or signed, plus retained signed originals. Ready-for-review, superseded and revoked versions are hidden |
| `GET documents/<id>/pdf/` or `page/?sha256=&page=` | The version's PDF or a page image (same caching/throttle as manager previews) |
| `GET originals/<id>/pdf/` | A retained signed original |
| `GET invoices/` (`?unpaid=true`), `invoices/<id>/` | Invoices with lines; detail adds payments and issuer |
| `GET invoices/<id>/info/`, `pdf/`, `page/` | Saved invoice version metadata, PDF, page image. Reuses the saved version unless the invoice changed. Void invoices have no PDF |
| `GET payments/`, `payments/<id>/` | Payment history and the receipt (issuer, property/unit, current balance). Reversed payments show `reversed: true` |
| `GET/POST maintenance/` (`?open=true`) | The tenant's repairs; POST reports one for their current lease (`lease` is required only with several current leases) |
| `GET maintenance/<id>/` | Detail with photos and non-internal updates (`from_you` marks the tenant's own messages) |
| `POST maintenance/<id>/updates/` or `photos/` | A message or a photo (JPEG/PNG/WebP, 8 MB, eight per request) while the repair is open |

Lists use the standard pagination envelope. Tenant-facing serializers in `apps/portal/serializers.py` list fields explicitly: manager notes, identity numbers, repair cost estimates, vendor contacts, who recorded a payment and reversal reasons are never included.

## Deliberate limits

- Signing stays on the emailed, code-verified link; the portal only shows that a signature is awaited.
- Paying online arrives with the Lenco integration. Until then the portal shows balances and receipts only.
- A tenant writes at most 60 times an hour across repairs, messages, photos and profile changes.

Tests: `backend/apps/portal/tests.py` (access boundaries, cross-tenant 404s, hidden drafts/documents/notes, PDF reuse, repair flow, phone uniqueness, access removal, overview query budget).
