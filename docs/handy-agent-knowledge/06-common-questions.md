# Common questions and calculations

## Occupancy

- Occupied units: units with `occupancy_status = occupied`.
- Vacant units: units with `occupancy_status = vacant`.
- Occupancy rate: occupied units divided by all units in scope, multiplied by 100.
- When identifying who occupies a unit, use its active lease rather than status alone.

## Rent roll

The current contractual rent roll is the sum of `monthly_rent` for active leases in scope. A unit's `rent_amount` is an expected amount and should not replace an active lease's agreed `monthly_rent`.

## Outstanding and arrears

- Invoice balance: `total - amount_paid`.
- Outstanding: sum balances for open and partially paid invoices.
- Arrears or overdue: outstanding invoices whose `due_date` is before today.
- Exclude void invoices.

## Collections

Sum `billing_payment.amount` for the requested payment-date range where `reversed_at` is null. Say whether the answer uses payment date, invoice month, or invoice issue date.

## Property performance

Always restrict properties, units, leases, invoices, and payments to the authorized organization first. State the period and currency. Do not compare organizations.

## Ambiguous requests

- Ask which property, unit, tenant, invoice, or period the user means when multiple matches exist.
- Before an action, summarize the selected records and important amounts or dates.
- For a payment, repeat tenant, invoice reference, amount, method, payment date, and resulting balance before approval.
- For an invoice, repeat tenant, lease or unit, each charge line, issue date, due date, and total before approval.

