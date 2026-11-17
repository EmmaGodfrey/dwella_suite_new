# Approved assistant actions

Dwella exposes a narrow action API. The assistant must fill the proposed action, show it to the user, and call it only after approval.

## Available actions

1. Create a property in the property manager's workspace. Do not ask for an owner.
2. Create a unit in an authorized property.
3. Create a tenant without automatically creating or activating a lease.
4. Create a draft lease. It always remains `draft`.
5. Create an invoice for an authorized tenant.
6. Record a manual payment against an authorized invoice.
7. Create a maintenance vendor.
8. Create a maintenance request.
9. Add a maintenance comment.
10. Preview a notice to 1–100 active workspace tenants: channel (`email`, `sms`,
    `whatsapp`), tenant public IDs, subject and plain-text body. Use
    `POST /api/v1/assistant/message-previews/`. Present all returned recipients,
    addresses, content and readiness. This action does not send anything.
11. After the user explicitly approves that exact preview, confirm it with
    `POST /api/v1/assistant/message-previews/{id}/confirm/` and `confirmed: true`.
    Previews expire in 30 minutes. Repeating confirmation does not create another
    delivery. Unconnected channels remain held; never describe held or queued
    requests as sent. SMTP acceptance does not prove delivery to the recipient.

## Role and property scope

- Property admins may use enabled actions throughout their workspace.
- Property managers may use enabled actions only for assigned properties and
  properties in a currently active cover session. Dwella rechecks live scope on
  every write and records covered-property changes in its audit trail.
- Creating a new workspace-wide property is reserved for a property admin.
- Property managers may create tenants; Dwella records who created an unplaced
  tenant so the manager can continue that setup. Leases, invoices, payments,
  maintenance requests and comments must stay within the manager's current
  property scope.
- If an action is denied, explain the permission or assignment requirement.
  Never retry using another user's token or another workspace.

## Safety behavior

- Only active property-admin and property-manager tokens may act. Tenant tokens
  are not issued. Platform admins need an explicitly authorized support context.
- Super admins without an authorized organization, and tenants, cannot act.
- Every action rechecks the user's live membership and organization.
- References to records in another organization are rejected.
- Retried requests are idempotent and must not create duplicate payments or invoices.
- Successful actions are written to Dwella's audit log.
- A successful HTTP response confirms the action was recorded. For messages,
  read the delivery state: HTTP success alone does not prove sending or delivery.

Messages are outbound notices, not an inbound chat platform. Do not query private
message tables directly. Use the approved action response. Re-preview when the
user changes the content/recipients or when contact details change. Never confirm
a different preview without asking the user to review it. Use a stable
Idempotency-Key when retrying either action.

## Financial confirmation

Creating an invoice changes the tenant's balance. Recording a payment changes that balance and creates a receipt. Treat both as high-attention actions and clearly present all financial details before approval.

## Environment and response handling

Use only operations marked `x-agent.enabled` in the connected environment's
schema. Test action URLs include `/test/api/v1/assistant/`; production uses
`/api/v1/assistant/`. Never switch environments to bypass a denial or missing
operation, and never send a test token to production.

Read `success`, `response_code`, `response_message` and `response_data` in the
standard response envelope. Validation or authorization failure is not success.
On an uncertain network result, retain the same Idempotency-Key when retrying
the same approved payload. Do not create a new request to bypass a conflict.
For notices, report the returned state: held, queued, provider-accepted,
delivered, failed and unknown outcomes are distinct.

