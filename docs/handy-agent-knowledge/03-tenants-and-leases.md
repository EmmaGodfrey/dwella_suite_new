# Tenants and leases

## `tenants_tenant`

One row is one tenant or applicant within an organization. Phone numbers are normalized and unique per organization.

Tenant statuses:

- `applicant`: created but not currently renting under an active lease.
- `active`: has an active lease.
- `past`: no longer has an active lease.

`national_id` and `tpin` are sensitive. TPIN is used for fiscal invoices when applicable. Do not show either field unless the authorized user specifically needs it for a legitimate property-management task.

## `leases_lease`

A lease links one tenant to one unit and stores the agreed terms.

Lease statuses:

- `draft`: being prepared and not active.
- `pending_signature`: awaiting signatures and not active.
- `active`: currently governs occupancy.
- `ended`: historical lease that has finished.

Draft, pending-signature, and active leases all hold the unit, so a unit cannot have a second open lease. `end_date` must be later than `start_date`, and `rent_due_day` is from 1 through 28.

Activating a lease marks the unit occupied and the tenant active. Ending an active lease marks the unit vacant and marks the tenant past when they have no other active lease.

The assistant may create draft leases only. It may not activate, end, or delete leases.

