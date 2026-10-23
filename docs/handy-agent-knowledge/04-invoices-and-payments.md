# Invoices, charges, and payments

## `billing_invoice`

An invoice records an amount owed by one tenant. It may be linked to a lease and unit. `total` is the sum of its invoice lines, `amount_paid` is the sum of non-reversed payments, and balance is `total - amount_paid`.

Invoice statuses:

- `open`: nothing has been paid and money remains due.
- `partially_paid`: some money has been paid and a balance remains.
- `paid`: the invoice is fully paid.
- `void`: cancelled financial record; exclude it from live balances.

An invoice is overdue when it is open or partially paid and `due_date` is before today. Overdue is calculated, not stored as a separate status.

`period_start` identifies the rent month for generated rent invoices. It is empty for one-off charges. Only one non-void rent invoice may exist for a lease and period.

## `billing_invoiceline`

Invoice lines explain the total. Kinds are:

- `rent`
- `late_fee`
- `utility`
- `deposit`
- `other`

Every line amount must be greater than zero.

## `billing_payment`

A payment is always recorded against an existing invoice. It is not recorded directly against a tenant without an invoice.

Payment methods are `cash`, `mobile_money`, `bank_transfer`, `card`, and `cheque`.

A valid payment:

- Has an amount greater than zero.
- Is not dated in the future.
- Does not exceed the invoice's remaining balance.
- Is not applied to a void invoice.

`reference` stores a mobile-money transaction ID, bank reference, cheque number, or similar external reference. A reversal preserves the original payment and sets `reversed_at`; reversed payments do not count toward collections or invoice amount paid.

The assistant may create an invoice and record a payment only after explicit approval. It may not void invoices, reverse payments, generate monthly invoices in bulk, or submit fiscal records to ZRA.

