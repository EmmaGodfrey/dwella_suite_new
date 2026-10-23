# Dwella Suite overview

Dwella Suite is a multi-organization property management system for landlords. Dwella has exactly three account types: super admins (Dwella staff), landlords, and tenants. There is no separate property-owner record: the landlord who owns the workspace is the owner of every property in it. Never ask for a property owner. Every portfolio record belongs to one organization. Never combine or compare private records across organizations unless a future audited support workflow explicitly allows it.

## Core business chain

1. A landlord's workspace (organization) contains properties.
2. A property contains units.
3. A tenant may be linked to a unit through a lease.
4. A lease defines dates, rent, deposit, due day, late-fee terms, and notice terms.
5. Invoices create amounts owed by tenants. Invoice lines explain each charge.
6. Payments are recorded against invoices and reduce the invoice balance.
7. Maintenance requests belong to a property and may also identify a unit, tenant, and vendor.

## Identifiers

- Internal integer `id` values are database keys. Use them only for joins and row-access rules.
- Public API identifiers are UUID values stored in `public_id`. Use public IDs when calling Dwella actions.
- Human references such as `INV-0001`, `RCT-0001`, `LSE-0001`, and `MR-0001` are display references, not database keys.

## Currency and time

- Use the organization's `currency`; the Zambia default is `ZMW`.
- Monetary values are decimal amounts. Never treat them as floating-point approximations.
- Business dates and user-facing timestamps use the organization's timezone; the Zambia default is `Africa/Lusaka`.

## Answering rules

- Prefer current stored statuses and amounts over guesses.
- State the date range used for totals.
- A tenant balance is the sum of `invoice.total - invoice.amount_paid` for open or partially paid invoices.
- An invoice is overdue only when its status is open or partially paid and its `due_date` is before today.
- Exclude void invoices from billed and outstanding totals.
- Exclude payments where `reversed_at` is set when calculating money collected.
- Do not claim that an action happened unless the action API returned success.

