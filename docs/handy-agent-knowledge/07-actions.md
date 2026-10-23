# Approved assistant actions

Dwella exposes a narrow action API. The assistant must fill the proposed action, show it to the user, and call it only after approval.

## Available actions

1. Create a property. Do not ask for an owner; the landlord's workspace owns it.
2. Create a unit in an authorized property.
3. Create a tenant without automatically creating or activating a lease.
4. Create a draft lease. It always remains `draft`.
5. Create an invoice for an authorized tenant.
6. Record a manual payment against an authorized invoice.
7. Create a maintenance vendor.
8. Create a maintenance request.
9. Add a maintenance comment.

## Safety behavior

- Only landlord tokens (`organization_admin` and `portfolio_manager`) may act.
- Super admins without an authorized organization, and tenants, cannot act.
- Every action rechecks the user's live membership and organization.
- References to records in another organization are rejected.
- Retried requests are idempotent and must not create duplicate payments or invoices.
- Successful actions are written to Dwella's audit log.
- A successful HTTP response is the only proof that an action completed.

## Financial confirmation

Creating an invoice changes the tenant's balance. Recording a payment changes that balance and creates a receipt. Treat both as high-attention actions and clearly present all financial details before approval.

