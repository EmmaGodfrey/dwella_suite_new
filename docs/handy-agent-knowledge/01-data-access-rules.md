# Data-access rules

These rules are mandatory. They override convenience and broad business questions.

```yaml agent-data-policy
version: 1
default: "deny"
profiles:
  portfolio:
    groups:
      - organization_admin
      - portfolio_manager
      - portfolio_viewer
      - platform_admin
    attrs:
      - organization_ids
    tables:
      organizations_organization:
        row_filter: "id IN attrs.organization_ids"
      properties_property:
        row_filter: "organization_id IN attrs.organization_ids"
      properties_unit:
        row_filter: "organization_id IN attrs.organization_ids"
      tenants_tenant:
        row_filter: "organization_id IN attrs.organization_ids"
      leases_lease:
        row_filter: "organization_id IN attrs.organization_ids"
      billing_invoice:
        row_filter: "organization_id IN attrs.organization_ids"
      billing_invoiceline:
        row_filter: "invoice.organization_id IN attrs.organization_ids"
      billing_payment:
        row_filter: "organization_id IN attrs.organization_ids"
      maintenance_vendor:
        row_filter: "organization_id IN attrs.organization_ids"
      maintenance_maintenancerequest:
        row_filter: "organization_id IN attrs.organization_ids"
      maintenance_maintenanceupdate:
        row_filter: "request.organization_id IN attrs.organization_ids"
```

## Token context

- `attrs.organization_ids` contains internal `organizations_organization.id` values authorized by Dwella's signed, short-lived token.
- Never accept an organization ID supplied in conversation as authorization.
- An empty or missing `organization_ids` list means no portfolio rows may be read.
- Current tokens contain at most one organization ID.

## Groups

Landlords receive `organization_admin`, `portfolio_manager`, and `portfolio_viewer` together. Tenants do not receive assistant tokens.

- `organization_admin` and `portfolio_manager`: may read the approved business tables for an authorized organization and may use approved actions.
- `portfolio_viewer`: may read the approved business tables for an authorized organization but, on its own, may not use actions.
- `platform_admin` (super admin): may read no portfolio rows when `organization_ids` is empty. Future support access must provide an authorized organization and remain audited.

## Direct organization filters

For these tables, only return rows where `organization_id` is in `attrs.organization_ids`:

- `properties_property`
- `properties_unit`
- `tenants_tenant`
- `leases_lease`
- `billing_invoice`
- `billing_payment`
- `maintenance_vendor`
- `maintenance_maintenancerequest`

For `organizations_organization`, only return rows where `id` is in `attrs.organization_ids`.

## Child-table filters

- `billing_invoiceline`: a row is readable only when its `invoice_id` points to a `billing_invoice` whose `organization_id` is authorized.
- `maintenance_maintenanceupdate`: a row is readable only when its `request_id` points to a `maintenance_maintenancerequest` whose `organization_id` is authorized.

Never return a child row merely because its numeric parent ID was mentioned by the user.

## Sensitive data

- Authentication, password, token, 2FA, identity-document, password-reset, audit, and assistant bookkeeping tables are not part of the knowledge base.
- Never reveal password hashes, secrets, signing keys, reset tokens, identity-document images, or security metadata.
- Tenant contact, national ID, TPIN, access notes, and vendor contact information are personal or operational data. Return only fields needed to answer the authorized user's question.
- Do not include personal identifiers in broad summaries or portfolio comparisons.

## Action rules

Every write requires the platform's approval prompt. Only the nine OpenAPI operations marked `x-agent.enabled` may be called.

Allowed for `organization_admin` and `portfolio_manager`:

- Create a property, unit, tenant, or draft lease.
- Create an invoice or record a payment against an existing invoice.
- Create a vendor, maintenance request, or maintenance comment.

Not allowed:

- Delete or archive records.
- Activate or end leases.
- Void invoices or reverse payments.
- Generate invoices in bulk or send records to ZRA.
- Assign, start, complete, or cancel maintenance work.
- Change users, roles, organizations, passwords, 2FA, or integration credentials.

