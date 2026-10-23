# Approved assistant actions

Dwella exposes a narrow action API. The assistant must fill the proposed action, show it to the user, and call it only after approval.

## Available actions

1. Create a property owner.
2. Create a property.
3. Create a unit in an authorized property.
4. Create a tenant without automatically creating or activating a lease.
5. Create a draft lease. It always remains `draft`.
6. Create an invoice for an authorized tenant.
7. Record a manual payment against an authorized invoice.
8. Create a maintenance vendor.
9. Create a maintenance request.
10. Add a maintenance comment.

## Safety behavior

- Only `organization_admin` and `portfolio_manager` tokens may act.
- `portfolio_viewer` tokens are read-only.
- Every action rechecks the user's live membership and organization.
- References to records in another organization are rejected.
- Retried requests are idempotent and must not create duplicate payments or invoices.
- Successful actions are written to Dwella's audit log.
- A successful HTTP response is the only proof that an action completed.

## Financial confirmation

Creating an invoice changes the tenant's balance. Recording a payment changes that balance and creates a receipt. Treat both as high-attention actions and clearly present all financial details before approval.

