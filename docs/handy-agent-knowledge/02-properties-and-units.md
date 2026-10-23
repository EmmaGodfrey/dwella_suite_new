# Properties, owners, and units

## `properties_propertyowner`

A property owner is the person or entity on whose behalf a portfolio property is managed. The owner may be empty on a property. Contact fields are private and should be shown only when relevant.

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

