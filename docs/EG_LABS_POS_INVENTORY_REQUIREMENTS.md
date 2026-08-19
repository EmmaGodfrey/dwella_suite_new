# EG Labs Small Business POS + Inventory
## Product Requirements & Technical Specification
**Document purpose:** Codex-ready implementation specification  
**Product:** Small Business POS + Inventory / Business Operations Suite  
**Parent:** EG Labs  
**Primary market:** Zambia initially  
**Recommended backend:** Django + Django REST Framework  
**Architecture:** Multi-tenant modular monolith with offline-capable clients

---

# 1. Product Vision

Build a simple business operations platform for small and medium-sized businesses that need to manage:

- Sales
- Cashiers
- Stock
- Purchases
- Suppliers
- Customers
- Expenses
- Cash and payment methods
- Daily reconciliation
- Reports

The product should be easier than a traditional ERP while providing enough control for a business owner to understand what is happening in their business.

Target customers include:

- Mini-marts
- Boutiques
- Hardware stores
- Spare-parts shops
- Salons/barbershops
- Pharmacies where applicable
- Electronics shops
- Small wholesalers
- Restaurants in a later vertical
- General retail stores

---

# 2. Product Principles

1. Fast to learn.
2. Fast checkout.
3. Mobile-friendly.
4. Works with unreliable internet.
5. Owners can see the business without being physically present.
6. Strong audit trail.
7. Stock cannot silently change.
8. Cash reconciliation must be simple.
9. Mobile money must be treated as a first-class payment method.
10. Product should grow into broader business operations software without starting as a massive ERP.

---

# 3. MVP Scope

MVP includes:

- Organizations
- Branches/stores
- Users and permissions
- Products
- Categories
- Inventory
- Stock movements
- Suppliers
- Purchases
- Customers
- POS sales
- Returns
- Expenses
- Cash register sessions
- Payment-method reconciliation
- Dashboard
- Reports
- Audit trail
- Offline synchronization foundations

MVP excludes:

- Full accounting/general ledger
- Payroll
- HR
- Manufacturing
- CRM automation
- E-commerce storefront
- Complex warehouse management
- Loyalty points
- Native payment processing
- ZRA integration in first implementation milestone

---

# 4. Roles

### Organization Owner
Full access.

### Administrator
Manages branches, users, products, settings.

### Branch Manager
Manages assigned branch and reports.

### Cashier
Can:
- Open register
- Make sales
- Accept payments
- Print/share receipt
- Process allowed returns
- Close register

Cannot:
- Edit historical sales
- Change cost prices unless granted
- Perform stock adjustments unless granted
- View all company financial reports unless granted

### Inventory Officer
Can:
- Receive stock
- Adjust stock
- Create stock counts
- Transfer stock
- Manage products
- Manage suppliers

### Accountant / Finance
Can:
- View reports
- Manage expenses
- Review reconciliations
- Export transactions

### Read-only Owner
Can view dashboards/reports.

---

# 5. Multi-Tenancy

Each organization is isolated.

All business records must include organization ownership.

Branch-level records must include branch ownership where relevant.

Use:
- Shared database
- Shared schema
- Organization scoping
- UUID identifiers externally

Prevent all cross-organization access.

---

# 6. Organization

Fields:

- Name
- Logo
- Phone
- Email
- Currency
- Timezone
- Address
- Business registration details
- Tax details
- Receipt settings
- Inventory settings
- Negative-stock policy
- Pricing settings

---

# 7. Branch / Store

A business may have one or more branches.

Fields:

- Organization
- Branch code
- Name
- Address
- Phone
- Active status
- Default warehouse/location
- Receipt header/footer

MVP can allow one branch by default but multi-branch should be supported from the data model.

---

# 8. Product Catalog

## 8.1 Product

Fields:

- SKU
- Barcode
- Name
- Description
- Category
- Brand optional
- Unit of measure
- Cost price
- Selling price
- Tax category
- Track inventory boolean
- Minimum stock
- Reorder level
- Active status
- Image optional

Product types:

- Stock item
- Non-stock item
- Service

Future:
- Variants
- Serial numbers
- Batches
- Expiry dates

---

# 9. Product Categories

Fields:

- Name
- Parent category optional
- Description
- Active status

Support nested categories later.

---

# 10. Inventory

Inventory must not be represented only as a mutable quantity field.

Maintain a stock movement ledger.

## 10.1 Stock Movement

Every inventory change must create a movement.

Movement types:

- Opening stock
- Purchase receipt
- Sale
- Sale return
- Purchase return
- Adjustment increase
- Adjustment decrease
- Transfer out
- Transfer in
- Stock count adjustment
- Damage
- Expiry
- Other

Fields:

- Organization
- Branch/location
- Product
- Movement type
- Quantity
- Unit cost where applicable
- Reference entity/type
- User
- Timestamp
- Notes

Current stock can be cached, but the movement ledger remains the source of truth.

---

# 11. Stock Adjustments

Adjustment requires:

- Product
- Quantity
- Increase/decrease
- Reason
- User
- Approval depending on permissions
- Timestamp

Reasons:

- Damage
- Theft/loss
- Counting correction
- Expiry
- Internal use
- Data correction
- Other

Every adjustment must be audited.

---

# 12. Stock Counts

Support periodic stock-taking.

Workflow:

1. Create stock count
2. Select branch/location
3. Freeze expected quantities snapshot
4. Staff enter counted quantities
5. Show variance
6. Review
7. Approve
8. Generate stock adjustment movements

Statuses:

- Draft
- In progress
- Review
- Approved
- Cancelled

---

# 13. Suppliers

Fields:

- Name
- Contact person
- Phone
- Email
- Address
- Tax information optional
- Notes
- Active status

---

# 14. Purchasing

## 14.1 Purchase order

Fields:

- Supplier
- Branch
- PO number
- Date
- Expected date
- Status
- Items
- Notes
- Created by

Statuses:

- Draft
- Submitted
- Partially received
- Received
- Cancelled

## 14.2 Goods receipt

Receiving stock must:

- Record quantities received
- Allow partial receiving
- Record cost
- Generate stock movements
- Update inventory
- Preserve supplier reference/document
- Audit the operation

MVP may allow "Receive purchase" without a formal PO, but purchase orders should exist in the domain model.

---

# 15. Customers

Customer fields:

- Name
- Phone
- Email
- Address
- Notes
- Customer code
- Active status

MVP:
- Optional customer on retail sale

Future:
- Credit accounts
- Customer balances
- Loyalty
- Statements

---

# 16. POS Sale

Sale fields:

- Sale number
- Branch
- Register
- Cashier
- Customer optional
- Date/time
- Line items
- Subtotal
- Discount
- Tax
- Total
- Payment status
- Sale status
- Notes

Line item:

- Product
- SKU snapshot
- Description snapshot
- Quantity
- Unit price
- Discount
- Tax
- Line total
- Cost snapshot

Historical sale details must not change if the product is later renamed or repriced.

---

# 17. POS Workflow

Primary checkout workflow:

1. Open POS
2. Scan barcode or search product
3. Add products
4. Change quantities
5. Apply permitted discount
6. Select customer optional
7. Press Pay
8. Split/select payment method
9. Complete sale
10. Generate receipt
11. Deduct inventory
12. Update register session totals

Target:
- Common sale completion in a few seconds

POS UI must be keyboard and touch friendly.

---

# 18. Payment Methods

MVP payment methods:

- Cash
- MTN Mobile Money
- Airtel Money
- Bank transfer
- Card
- Other

Support split payments.

Example:

```text
Sale total: K1,000
Cash: K300
MTN Mobile Money: K700
```

Fields per payment:

- Method
- Amount
- Reference optional
- Timestamp

---

# 19. Cash Register Sessions

A cashier must open a register session.

## 19.1 Opening

Fields:

- Branch
- Register
- Cashier
- Opening cash
- Open time

## 19.2 During session

Track:

- Cash sales
- Non-cash sales
- Cash refunds
- Cash paid in
- Cash paid out
- Expected cash

## 19.3 Closing

Cashier enters actual counted cash.

System calculates:

- Expected cash
- Actual cash
- Difference
- Over/short

Manager can review.

Session statuses:

- Open
- Closing review
- Closed

Closed sessions must not be edited except through audited correction workflow.

---

# 20. Daily Payment Reconciliation

Provide a reconciliation screen by branch/date.

Show:

- Cash expected
- Cash counted
- MTN sales total
- Airtel sales total
- Card total
- Bank transfer total
- Other total

Allow user to enter actual settlement/account values where useful.

Show differences.

Future:
- Mobile money provider statement imports
- Bank statement imports
- Automatic matching

---

# 21. Sales Returns and Refunds

A return must reference the original sale where possible.

Support:

- Full return
- Partial return
- Exchange later
- Refund to payment method
- Store credit later

Return action must:

- Create a return record
- Generate inventory movement
- Create refund/payment reversal record
- Preserve original sale
- Create audit entry

Never delete the original sale.

---

# 22. Discounts

Discount types:

- Line percentage
- Line fixed amount
- Sale percentage
- Sale fixed amount

Permissions:

- Cashier discount limit
- Manager override

Audit high-value or manual discounts.

---

# 23. Expenses

Expense fields:

- Branch
- Category
- Description
- Amount
- Date
- Payment method
- Supplier optional
- Receipt attachment
- User
- Notes

Categories:

- Rent
- Electricity
- Water
- Transport
- Salaries later
- Repairs
- Supplies
- Marketing
- Miscellaneous

Expense reporting is operational reporting, not full accounting.

---

# 24. Dashboard

Owner dashboard:

### Today
- Sales
- Transactions
- Average basket
- Gross margin estimate
- Expenses
- Cash expected
- Cash variance
- Top products
- Low stock

### Period
- Sales trend
- Profit estimate
- Purchases
- Expenses
- Stock value
- Best sellers
- Slow movers
- Branch comparison
- Cashier performance

Filters:
- Branch
- Date range

---

# 25. Reports

Required reports:

1. Sales summary
2. Sales detail
3. Sales by product
4. Sales by category
5. Sales by cashier
6. Sales by branch
7. Payment methods
8. Returns
9. Discounts
10. Current stock
11. Stock movement
12. Stock adjustment
13. Low-stock report
14. Stock valuation
15. Purchases
16. Supplier purchases
17. Expenses
18. Register/session reconciliation
19. Gross profit estimate

Exports:
- CSV required
- PDF later

---

# 26. Receipts

Receipt includes:

- Business name/logo
- Branch
- Sale number
- Date/time
- Cashier
- Items
- Quantity
- Unit prices
- Discounts
- Tax where relevant
- Total
- Payment method(s)
- Amount tendered
- Change
- Customer optional
- Footer

Delivery options:

MVP:
- Print
- Download/share PDF/text representation where supported

Later:
- SMS
- WhatsApp
- Email

---

# 27. Offline Operation

Offline capability is important.

Recommended approach:

- Local client database
- Queue sales locally while offline
- Sync when connection returns
- Server remains authoritative
- Use globally unique client-generated transaction IDs
- Idempotent sync endpoints

The first backend implementation must support idempotency even if the first UI is online-only.

Critical rule:

A reconnect must never duplicate a sale.

---

# 28. Offline Sync Strategy

Each syncable entity should have:

- UUID
- Created timestamp
- Updated timestamp
- Version/revision
- Sync status where client-side
- Deleted/tombstone state where needed

Sales should be append-oriented.

For conflict handling:

- Financial transactions: avoid destructive merges
- Product master data: server-authoritative unless user has permission
- Inventory: synchronize movements, not arbitrary quantity replacement

---

# 29. ZRA Smart Invoice Readiness

Do not hard-code tax compliance logic directly into POS sale code.

Create an integration boundary such as:

```text
TaxFiscalizationService
```

Possible future implementations:

- No-op/local implementation
- ZRA Smart Invoice adapter
- Mock/test adapter

The domain sale should complete independently from provider-specific code where legally and operationally appropriate.

Implementation of live fiscalization must use the then-current official ZRA specifications and any required approval/accreditation processes.

---

# 30. Mobile Money Integration Readiness

Do not require direct API integration in MVP.

Initial flow:

- User selects MTN/Airtel
- Records transaction/reference if required
- Reconciles totals

Future adapter interface:

```text
PaymentProviderAdapter
```

Possible features:

- Payment request
- Confirmation callback
- Transaction lookup
- Settlement import
- Reconciliation

Provider credentials must be encrypted/secured.

---

# 31. Audit Trail

Audit:

- Product creation/update
- Cost price changes
- Selling price changes
- Stock adjustments
- Stock count approvals
- Purchase receiving
- Sale void/cancel
- Returns
- Discounts above threshold
- Cash paid in/out
- Register close
- Register correction
- Expense changes
- User/role changes
- Settings changes

Audit record fields:

- Organization
- Branch optional
- User
- Action
- Entity
- Old values
- New values
- Timestamp
- Request information
- Reason where required

---

# 32. Permissions

Implement explicit permission checks.

Examples:

- `products.view`
- `products.manage`
- `inventory.view`
- `inventory.adjust`
- `inventory.count`
- `sales.create`
- `sales.return`
- `sales.discount`
- `purchases.manage`
- `expenses.manage`
- `reports.view`
- `register.open`
- `register.close`
- `users.manage`

Avoid relying only on broad roles. Roles should map to granular permissions.

---

# 33. API Design

Prefix:

`/api/v1/`

Suggested resources:

```text
/auth/
/organizations/
/branches/
/users/
/products/
/categories/
/inventory/
/stock-movements/
/stock-adjustments/
/stock-counts/
/suppliers/
/purchase-orders/
/goods-receipts/
/customers/
/sales/
/returns/
/payments/
/registers/
/register-sessions/
/expenses/
/reports/
/audit-trail/
```

Use:

- Pagination
- Search
- Filtering
- Ordering
- OpenAPI
- Consistent errors
- Idempotency keys for critical transaction endpoints

---

# 34. Recommended Django Apps

```text
apps/
  accounts/
  organizations/
  branches/
  catalog/
  inventory/
  suppliers/
  purchasing/
  customers/
  sales/
  payments/
  registers/
  expenses/
  reports/
  audit/
  integrations/
  subscriptions/
  common/
```

Do not use microservices initially.

---

# 35. Background Jobs

Use Celery + Redis for:

- Report generation
- Email
- Low-stock notifications
- Scheduled summaries
- Integration retries
- Future fiscalization retries where permitted
- Future settlement imports
- Data exports

Jobs must be idempotent.

---

# 36. Data Requirements

Use:

- PostgreSQL
- Decimal for money
- UTC timestamps
- Organization-specific timezone
- UUID public IDs

Snapshot historical values on transaction lines:

- Product name
- SKU
- Unit price
- Cost
- Tax

This protects historical reporting from future catalog changes.

---

# 37. Inventory Valuation

MVP recommended valuation:

**Weighted average cost**

The system should:
- Update weighted cost when receiving stock
- Preserve cost snapshots on sale lines
- Calculate approximate gross profit

Do not attempt a full accounting ledger in MVP.

Future:
- FIFO if required

---

# 38. Security

Required:

- Tenant isolation
- Branch access control
- Secure authentication
- Rate limiting
- Audit logging
- File validation
- Environment secrets
- HTTPS
- No secret values in source control
- Permission tests
- Idempotency on transaction creation
- Database transactions

---

# 39. Non-Functional Requirements

## Performance

Target:
- Product search under 300 ms for normal datasets
- Sale completion API under 1 second excluding external integrations
- Dashboard under 2 seconds for common periods

## Scale target

Architecture should handle:

- Thousands of businesses
- Dozens of branches per business
- Hundreds of thousands of products platform-wide
- Millions of sales
- Tens of millions of stock movements

Do not prematurely optimize.

---

# 40. MVP UI Screens

At minimum:

1. Login
2. Dashboard
3. POS checkout
4. Products
5. Product form
6. Inventory
7. Stock adjustment
8. Stock count
9. Suppliers
10. Purchases
11. Customers
12. Sales history
13. Sale detail
14. Returns
15. Expenses
16. Register opening
17. Register closing
18. Reconciliation
19. Reports
20. Users
21. Settings
22. Audit trail

---

# 41. Phase 2

- Product variants
- Barcode label printing
- Customer credit
- Supplier balances
- Multi-warehouse
- Transfer workflows
- Batch/expiry tracking
- Serial tracking
- Loyalty
- SMS/WhatsApp receipts
- Advanced reconciliation
- Mobile app
- Full offline POS
- ZRA integration
- Payment-provider integrations

---

# 42. Phase 3

Potential expansion into a broader business suite:

- Accounting
- Payroll
- HR
- CRM
- Procurement
- E-commerce
- Restaurant module
- Service-business module
- Advanced analytics
- AI business assistant

The suite should evolve from customer demand.

Do not build these before validating the core POS/inventory product.

---

# 43. Testing Requirements

Must include tests for:

- Organization isolation
- Branch permissions
- Product CRUD
- Stock movement calculations
- Stock adjustments
- Stock count approval
- Goods receipt
- Sale creation
- Split payment
- Return/refund
- Register expected cash
- Register closing variance
- Offline duplicate prevention/idempotency
- Gross profit calculation
- Audit events

Critical invariant tests:

1. Inventory cannot change without a stock movement.
2. A completed sale cannot silently mutate.
3. A return does not delete the original sale.
4. Retrying a sale request with the same idempotency key does not create a duplicate.
5. Organization A can never access Organization B records.

---

# 44. Codex Implementation Instructions

Codex should:

1. Use Django + Django REST Framework.
2. Use PostgreSQL.
3. Use Celery + Redis.
4. Implement a modular monolith.
5. Keep domain/business logic out of API views.
6. Use service functions/classes for transactions.
7. Use database transactions for sales, payments, returns, goods receipts, and stock counts.
8. Implement idempotency for transaction creation.
9. Implement organization scoping centrally.
10. Implement granular permissions.
11. Create stock movements for every inventory mutation.
12. Add tests with each module.
13. Generate OpenAPI documentation.
14. Add Docker local development.
15. Add fixtures/factories.
16. Add linting, formatting, tests, and migration checks for CI.
17. Avoid microservices.
18. Avoid building accounting/payroll/CRM before core workflows are complete.
19. Prefer explicit readable code.
20. Document key domain invariants.

---

# 45. First End-to-End Milestone

The initial implementation is complete when a business can:

1. Register organization
2. Create branch
3. Create cashier
4. Create products
5. Enter opening stock
6. Receive a purchase
7. Open cash register
8. Sell products
9. Accept split cash/mobile-money payment
10. Generate receipt
11. Observe stock reduction
12. Process a partial return
13. Observe stock restoration
14. Record an expense
15. Close register
16. View expected vs actual cash
17. View sales report
18. View inventory report
19. View gross profit estimate
20. View complete audit trail

Build and test this workflow before expanding scope.
