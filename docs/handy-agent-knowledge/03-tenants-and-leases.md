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

Draft, pending-signature, and active leases hold the unit against unrelated
leases. The supported renewal workflow may prepare one linked future agreement
while the current lease is active; it does not permit two active leases on a
unit. `end_date` must be later than `start_date`, and `rent_due_day` is 1 through 28.

Activating a lease marks the unit occupied and the tenant active. Ending an active lease marks the unit vacant and marks the tenant past when they have no other active lease.

The assistant may create draft leases only. It may not activate, end, or delete leases.

## Renewals, archiving and portal access

`renewal_of_id` links a renewal to the previous agreement. The application's
renewal workflow keeps the same tenant/unit and starts the new draft the day
after the active agreement ends. Signing and the start date govern activation;
preparing a renewal does not make it active or count its rent twice. Use only
active leases for the current contractual rent roll. Handy has no renewal,
signing or activation action; guide the manager to the lease screen.

The inherited `is_active` flag distinguishes archived tenant records from active
records and is separate from tenant rental status. Preserve archived records
for historical invoices/payments. Limit current-tenant questions to non-archived
records unless the user explicitly asks for history. A linked `user_id` is not
by itself proof of current portal permission; the app rechecks live access.

