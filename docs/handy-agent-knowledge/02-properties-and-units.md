# Properties and units

Properties have no separate owner record. They belong to a Dwella workspace;
this does not establish legal ownership. Never ask for or record a property
owner through the assistant. Property admins can see the whole workspace.
Property managers can see and update only assigned properties and properties
they are actively covering for a teammate.

## `properties_property`

One row is one physical or managed property.

Property types:

- `apartment`: apartment building or apartment portfolio property.
- `house`: standalone residential house.
- `commercial`: retail, office, industrial, or other commercial property.
- `mixed_use`: combines residential and commercial use.
- `land`: undeveloped or managed land.

Management statuses:

- `managed`: actively under management.
- `prospect`: not yet an active managed property.
- `archived`: retained for history and normally excluded from active portfolio totals.

Property names must be unique inside an organization.

Creating a new workspace-wide property is a property-admin action. A property
manager should ask an admin to add a property and assign it to them.
For a CSV, use Handy's property import preview and confirmation actions. The
preview reports counts and validation issues without creating records; property
imports remain property-admin only.

## `properties_unit`

One row is one rentable or managed space inside a property. Unit names are unique within their property.

Occupancy statuses:

- `vacant`: no current active occupancy.
- `occupied`: occupied by a tenant, normally through an active lease.
- `maintenance`: unavailable because of maintenance.
- `reserved`: held for a future occupant or purpose.

`rent_amount` is the unit's expected monthly rent. A lease may copy or override
this amount through `monthly_rent`. A property manager may create or update a
unit only when the unit's property is in their current assigned/covered scope.
For a CSV of units, use Handy's import preview, show the summary, and wait for
explicit approval before confirmation. Managers can import only into assigned or
actively covered properties.

Do not infer a tenant from `occupancy_status` alone. Use an open lease to identify the tenant.

