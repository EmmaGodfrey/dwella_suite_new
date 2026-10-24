# Subscription and paywall foundation

User direction, 24 October 2026: selected features will require a subscription. Pricing may be unit-based or another model; paid feature selection, tier names, prices and the SaaS billing provider are undecided. Lenco tenant rent collection is a separate concern from charging property managers for Dwella.

## Boundaries

- Account roles answer **who may perform an action**. Workspace entitlements answer **whether that workspace has a capability**. Both checks are required. Subscription access must never turn a tenant into a manager or give support staff unrestricted customer access.
- `subscriptions.WorkspaceAccessPolicy` stores only feature overrides and capacity limits for one organization. A future plan catalogue, trial/renewal lifecycle, billing meter and verified subscription webhook can translate their decisions into this policy. No provider, price, plan label or billing interval is embedded in feature code.
- All registered capabilities default to available during the current beta, with unlimited record capacity. No paid boundary is activated by this migration. Explicit superuser changes can disable a feature, set an expiry or restrict capacity. Register new paid-only features with deliberate defaults once commercial policy is chosen; do not assume a missing grant implies payment.
- Role checks, workspace isolation, suspension and CSRF remain authoritative. Manager access metadata is read-only; tenants cannot read workspace-wide usage or change grants. A server 403 includes `feature_unavailable`/`capacity_exceeded` and the relevant key/reason for a future upgrade UI.

## Registered capabilities and current integration

| Key | Current guard / future integration point |
| --- | --- |
| `lease_documents` | Enforced when preparing a new lease document |
| `lease_signing` | Enforced when issuing/replacing a tenant signing invitation |
| `bulk_imports` | Registered for the approved future importer; check before preview/confirmation as appropriate |
| `tenant_portal` | Registered for future tenant self-service; design onboarding/access policy before applying it |
| `online_payments` | Registered for starting future checkout; provider confirmations for already initiated payments must still be processed |
| `email_messages`, `sms_messages`, `whatsapp_messages` | Registered for future manager/scheduled communication; transactional recovery/signing mail is separate |

`require_feature(organization, Feature.… )` enforces a domain operation. `FeatureAccessMixin` adds optional view/action checks **after** existing role permissions. Alternate routes, assistant actions, imports and scheduled jobs must use the same service checks; hiding a browser button is not enforcement. Registry entries for unfinished features do not implement those features.

Feature rules have `enabled` and optional offset-aware `expires_at`. Expired or malformed configured rules fail closed. Existing grants are read freshly from the database; there is no long-lived backend entitlement cache or browser-persisted entitlement state.

Document/PDF access and history do not depend on a premium feature check. Signing invitations already issued can continue through the existing recipient verification/signature flow after an entitlement downgrade, subject to the original security/expiry/revocation checks. New invitations and new document preparation can be denied. No historical document or payment is deleted by changing policy, and a subscription restriction does not suspend the entire organization.

## Capacity and future unit-based pricing

Optional `properties`, `units` and `tenants` limits count **stored records**, including archived records. `null` means unlimited; zero means no additional records. These are technical capacity limits, not a decision about which units will be billable. Future billable-unit rules, prorating, usage periods and prices belong in a separate billing layer.

`capacity_guard(organization, Resource.…, additional=n)` locks organization then access policy inside the transaction and holds those locks through creation. It checks expected batch size and actual record growth before commit. Existing records remain readable/editable when usage exceeds a reduced limit. It never deletes excess records.

Current property/unit/tenant serializers and the first-property setup flow use this guard. Assistant unit/tenant/property creation inherits those serializers, so it cannot bypass capacity. Future bulk imports must use the same guard around the full atomic batch rather than checking usage once outside the write transaction. Internal scripts/ORM writes are trusted and must explicitly use the guard if they should obey commercial limits; there is no model signal or universal database trigger.

## API

| Route | Permissions and behavior |
| --- | --- |
| `GET /api/v1/subscriptions/entitlements/` | Current manager workspace, or explicit valid support context; registered feature states plus usage/limits. No policy row is created by reading. |
| `GET /api/v1/platform/workspaces/{uuid}/entitlements/` | Platform superuser only; inspect a workspace policy snapshot |
| `PATCH /api/v1/platform/workspaces/{uuid}/entitlements/` | Platform superuser only; validated partial merge, atomic audit record and 30 writes/hour per user |

Example administration payload (illustrative capability/capacity settings, not agreed paid tiers):

```json
{
  "feature_overrides": {
    "bulk_imports": {"enabled": false},
    "sms_messages": {"enabled": true, "expires_at": "2030-01-01T00:00:00Z"}
  },
  "limits": {"units": 50}
}
```

Changes merge only supplied keys. Set a feature entry to `null` to restore its beta default; set a limit to `null` for unlimited capacity. Unknown keys, invalid dates, negative/fractional/boolean limits and unexpected fields are rejected before any write. Successful changes and their before/after policy are audited; audit failure rolls the change back. Use these endpoints only for explicit operational decisions, not a client-provided claim of payment.

Frontend `Services/subscriptions.js` supplies `useWorkspaceEntitlementsQuery`. Pure `shared/entitlements.js` helpers provide fail-closed display hints for unavailable/loading/expired data and record capacity. They add no plan picker, pricing, checkout or changed page layout. Future screens should combine these hints with existing role access and handle authoritative server denials, including refreshing after an upgrade.

## Validation

Checks cover defaults, organization/role boundaries, anonymous and forbidden writes, support-context reads, CSRF, malformed rules/limits, expiry, scoped capacity, alternate assistant/setup paths, atomic batch rollback, retained records/signers, audit failure, throttling and competing PostgreSQL creates for one remaining unit slot. Final validation on 24 October 2026: full SQLite suite **532 passed / four PostgreSQL-only concurrency skips**; full isolated PostgreSQL 17 suite **536 passed**, including competing writes. Django check, Ruff and migration consistency pass, as do the frontend production build and all **11** focused frontend tests. Existing framework/bundle-size warnings remain. No live billing, provider setup, paid tier activation, messages, push or deployment were performed by this foundation.
