# Properties and units

Properties have no separate owner record. They belong to the property manager's
workspace in Dwella; this does not establish legal ownership. Never ask for or
record a property owner through the assistant.

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

## `properties_unit`

One row is one rentable or managed space inside a property. Unit names are unique within their property.

Occupancy statuses:

- `vacant`: no current active occupancy.
- `occupied`: occupied by a tenant, normally through an active lease.
- `maintenance`: unavailable because of maintenance.
- `reserved`: held for a future occupant or purpose.

`rent_amount` is the unit's expected monthly rent. A lease may copy or override this amount through `monthly_rent`.

Do not infer a tenant from `occupancy_status` alone. Use an open lease to identify the tenant.

