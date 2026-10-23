# Maintenance

## `maintenance_vendor`

A vendor is a contractor used for maintenance work. `trade` describes the vendor's specialty. Contact fields are operational data and should be returned only when needed.

## `maintenance_maintenancerequest`

A maintenance request belongs to a property. A unit is optional for common-area work, and tenant and vendor links are optional.

Statuses:

- `new`: reported and not yet scheduled.
- `scheduled`: assigned or scheduled.
- `in_progress`: work has started.
- `completed`: work is finished.
- `cancelled`: request was closed without completion.

Priorities are `low`, `normal`, `high`, and `urgent`.

Categories are `plumbing`, `electrical`, `roofing`, `appliances`, `security`, `painting`, `pest_control`, `grounds`, and `general`.

Sources are `landlord`, `tenant`, `caretaker`, and `inspection`. Requests created by the assistant use the landlord source.

`permission_to_enter` and `access_notes` affect physical access and must not be assumed. Do not tell a vendor they may enter unless the stored permission explicitly allows it.

## `maintenance_maintenanceupdate`

Updates form the request timeline. `comment` entries are messages; `status` entries record workflow changes. `is_internal` means the note is for the landlord's team and should not be presented as tenant-visible communication.

The assistant may create requests and comments. It may not assign vendors, start work, complete work, cancel requests, or charge repair costs to tenants.

