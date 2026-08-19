# Dwella Property Management Suite
## Product Requirements & Technical Specification
**Document purpose:** Codex-ready implementation specification  
**Product:** Dwella Property Management Suite  
**Parent:** EG Labs  
**Primary market:** Zambia initially, extensible to other African markets  
**Recommended backend:** Django + Django REST Framework  
**Architecture:** Multi-tenant modular monolith

---

# 1. Product Vision

Dwella Property Management Suite is a multi-tenant property operations platform for landlords, property managers, and real-estate agencies.

The product should help customers manage:

- Properties
- Units
- Tenants
- Leases
- Rent and charges
- Payments and arrears
- Expenses
- Maintenance
- Documents
- Communications
- Property owner statements
- Agent/property-manager operations
- Reporting

The first version should focus on property management, not the public property marketplace.

The future marketplace should be designed as an optional distribution layer that can consume property/unit data from the management suite without forcing the core product to depend on marketplace functionality.

---

# 2. Product Goals

## 2.1 Primary goals

1. Replace spreadsheets, notebooks, WhatsApp threads, and manual rent ledgers.
2. Give landlords and property managers a single source of truth.
3. Make it easy to determine:
   - Who owes rent
   - How much is owed
   - Which units are vacant
   - Which leases are expiring
   - Which maintenance issues are unresolved
   - How much a property earned
   - How much was spent on a property
4. Support multiple companies/organizations from one SaaS installation.
5. Preserve a complete audit trail of important business actions.
6. Provide a foundation for a future Dwella property marketplace.

## 2.2 Non-goals for MVP

Do not implement the following in the MVP:

- Public marketplace search
- Property bidding
- Mortgage origination
- Full accounting/general ledger
- Payroll
- Complex procurement
- Native payment processing
- AI pricing engine
- IoT/smart-home integrations
- Building access control
- Full CRM for property sales

---

# 3. User Roles

The system must support role-based permissions.

## 3.1 Platform roles

### Platform Administrator
Can:
- Manage organizations
- Manage subscriptions
- View platform-level metrics
- Access system logs
- Suspend organizations
- Configure global system settings

Platform administrators must not automatically access tenant financial or private data unless explicit support access is granted and audited.

## 3.2 Organization roles

### Organization Owner
Full access to the organization.

### Administrator
Can configure the organization and manage users.

### Property Manager
Can manage assigned properties, units, tenants, leases, maintenance, inspections, and communications.

### Accountant / Finance Officer
Can manage charges, rent payments, expenses, owner statements, financial reports, and reconciliations.

### Maintenance Officer
Can view and update assigned maintenance requests and work orders.

### Read-only Landlord / Property Owner
Can view selected properties, financial statements, maintenance status, occupancy, and reports.

### Tenant
Can access only their tenancy information, payment history, notices, lease documents, and maintenance requests.

---

# 4. Multi-Tenancy

The system must be multi-tenant.

Every organization-owned record must include an `organization_id`.

All queries must be scoped to the authenticated user's organization.

No user may access another organization's data by modifying URLs, IDs, API requests, or query parameters.

Recommended approach:
- Shared database
- Shared schema
- Row-level organization scoping at application layer
- UUID primary keys for externally exposed entities

Create reusable organization-scoping helpers/mixins.

---

# 5. Core Modules

## 5.1 Authentication and User Management

Required features:

- Email/password authentication
- Password reset
- Email verification
- Session/token management
- Optional MFA-ready architecture
- Organization invitations
- User activation/deactivation
- Role assignment
- Property-level access restrictions
- Last login tracking

Future:
- Google/Microsoft SSO
- Passkeys
- Enterprise SSO

---

# 6. Organization Management

Each organization must support:

- Legal/display name
- Logo
- Phone
- Email
- Physical address
- Currency
- Timezone
- Default rent frequency
- Default late fee rules
- Billing contact
- Company registration details
- Tax information
- Default document templates
- Organization settings

---

# 7. Property Management

## 7.1 Property entity

Required fields:

- ID
- Organization
- Property code
- Property name
- Property type
- Description
- Address
- Province
- District/city
- Latitude/longitude optional
- Property owner
- Management status
- Acquisition date optional
- Management start date
- Notes
- Created at
- Updated at
- Archived at

Property types should include:

- House
- Apartment building
- Flat
- Commercial property
- Office
- Retail
- Warehouse
- Mixed-use
- Land
- Other

## 7.2 Property owner

An organization may manage property on behalf of one or more owners.

Owner fields:

- Name
- Person/company type
- Email
- Phone
- Address
- Bank/payment details optional
- Tax identifier optional
- Notes

A property may have:
- One owner
- Multiple owners with ownership percentages

MVP may support one primary owner, but the data model should not prevent multiple owners later.

---

# 8. Unit Management

Each property may contain one or more units.

Unit fields:

- Unit ID
- Property
- Unit number/name
- Unit type
- Floor optional
- Bedrooms
- Bathrooms
- Area optional
- Furnished status
- Default monthly rent
- Deposit amount
- Status
- Description
- Amenities
- Meter numbers optional
- Notes

Unit statuses:

- Vacant
- Occupied
- Reserved
- Under maintenance
- Unavailable

The system must automatically derive occupancy where possible from active leases.

---

# 9. Tenant Management

Tenant fields:

- Full name
- Email
- Phone
- National ID/passport optional
- Date of birth optional
- Emergency contact
- Employer optional
- Residential address
- Notes
- Status
- Documents

Support multiple tenants on a lease.

Tenant portal account must be optional.

---

# 10. Lease Management

A lease connects:

- Organization
- Property
- Unit
- One or more tenants

Required lease fields:

- Lease number
- Start date
- End date
- Rent amount
- Rent frequency
- Rent due day
- Deposit required
- Deposit received
- Grace period
- Late fee rule
- Status
- Renewal status
- Notice period
- Notes

Lease statuses:

- Draft
- Pending
- Active
- Expiring
- Ended
- Terminated
- Cancelled

## 10.1 Lease workflows

### Create lease
1. Select property/unit
2. Select/add tenant
3. Define rent
4. Define deposit
5. Define term
6. Upload lease agreement
7. Save as draft
8. Activate

### Activate lease
When activated:
- Unit becomes occupied
- Recurring rent schedule is generated
- Deposit obligation is created if applicable
- Tenant receives notification if enabled
- Audit log entry is created

### Lease expiry
System must surface:
- Leases expiring in 30/60/90 days
- Lease already expired
- Renewal pending

---

# 11. Charges and Rent Ledger

The system requires a proper tenant ledger.

Charge types:

- Rent
- Deposit
- Utility
- Late fee
- Maintenance recharge
- Parking
- Service charge
- Other

Fields:

- Tenant
- Lease
- Property
- Unit
- Charge type
- Description
- Amount
- Due date
- Status
- Balance
- Created date
- Source
- Recurring schedule reference

Charge statuses:

- Pending
- Partially paid
- Paid
- Overdue
- Waived
- Cancelled

Recurring rent charges should be generated automatically.

Do not dynamically calculate old rent from the current lease amount. Historical charges must preserve the original amount.

---

# 12. Payments

Payment fields:

- Payment ID
- Tenant
- Lease
- Property
- Amount
- Date
- Payment method
- Reference
- Notes
- Received by
- Attachment/receipt optional
- Status

Supported payment methods:

- Cash
- Bank transfer
- Mobile money
- Card
- Cheque
- Other

A payment may be allocated across one or more outstanding charges.

Support:

- Full payment
- Partial payment
- Overpayment
- Unallocated credit
- Reversal

Payment reversal must never delete the original financial record.

Use immutable financial transaction records wherever practical.

---

# 13. Arrears

The system must calculate:

- Current outstanding balance
- Days overdue
- Total arrears by tenant
- Total arrears by property
- Aging buckets

Recommended aging:

- Current
- 1-30 days
- 31-60 days
- 61-90 days
- 90+ days

Dashboard must surface overdue tenants.

---

# 14. Receipts

The system should generate printable/downloadable receipts.

Receipt includes:

- Organization information
- Receipt number
- Tenant
- Property/unit
- Payment amount
- Payment date
- Payment method
- Reference
- Allocation details
- Balance after payment

Receipt numbering must be organization-specific.

---

# 15. Expenses

Expense fields:

- Property
- Category
- Supplier optional
- Description
- Amount
- Date
- Payment method
- Receipt/document
- Recoverable from tenant boolean
- Notes

Categories:

- Repairs
- Utilities
- Security
- Cleaning
- Insurance
- Property tax
- Management fees
- Contractor
- Landscaping
- Other

Reports must allow property income vs expenses.

---

# 16. Maintenance Management

## 16.1 Maintenance request

Fields:

- Ticket number
- Property
- Unit
- Tenant optional
- Title
- Description
- Category
- Priority
- Status
- Reported date
- Reported by
- Assigned user/vendor
- Estimated cost
- Actual cost
- Images/documents
- Resolution notes
- Completed date

Statuses:

- New
- Acknowledged
- Assigned
- In progress
- Waiting
- Completed
- Cancelled

Priorities:

- Low
- Medium
- High
- Emergency

Tenant portal must allow maintenance requests with images.

---

# 17. Vendors / Contractors

Vendor fields:

- Name
- Category
- Contact person
- Phone
- Email
- Address
- Notes
- Active status

Optional later:
- Vendor ratings
- Work history
- Preferred vendor per property

---

# 18. Inspections

Support:

- Move-in inspection
- Move-out inspection
- Routine inspection

Inspection fields:

- Property
- Unit
- Lease
- Inspection type
- Date
- Inspector
- Checklist
- Notes
- Photos
- Tenant acknowledgement optional

Future:
- Digital signature

---

# 19. Documents

Documents may attach to:

- Organization
- Property
- Unit
- Tenant
- Lease
- Payment
- Expense
- Maintenance ticket
- Inspection

Document metadata:

- Filename
- Type
- Uploaded by
- Uploaded at
- Related entity
- Visibility

Document types:

- Lease
- ID
- Receipt
- Invoice
- Inspection
- Ownership document
- Contractor quote
- Photo
- Other

Use object storage abstraction.

---

# 20. Notifications

Notification channels:

MVP:
- In-app
- Email

Later:
- SMS
- WhatsApp

Triggers:

- Rent due
- Rent overdue
- Payment recorded
- Receipt generated
- Lease expiring
- Maintenance status changed
- New maintenance request
- Organization invitation
- Document added

Notification templates must be editable in future.

---

# 21. Dashboard

Organization dashboard should show:

- Total properties
- Total units
- Occupied units
- Vacant units
- Occupancy rate
- Rent expected this month
- Rent collected this month
- Outstanding rent
- Overdue tenants
- Upcoming lease expiries
- Open maintenance requests
- Monthly income
- Monthly expenses
- Net property operating cash flow estimate

Allow filters:
- Date range
- Property
- Property owner

---

# 22. Reports

Required reports:

1. Rent roll
2. Tenant balances
3. Arrears aging
4. Payment history
5. Property income
6. Property expenses
7. Income vs expense
8. Occupancy
9. Vacancies
10. Lease expiries
11. Maintenance history
12. Owner statement

Reports should:
- Be filterable
- Export CSV
- Export PDF later
- Preserve organization scoping

---

# 23. Property Owner Statements

Generate owner statements by property and period.

Statement should show:

- Opening balance
- Rent collected
- Other income
- Expenses
- Management fees
- Adjustments
- Net amount due to owner
- Closing balance

MVP can generate statements manually.

Future:
- Automated monthly statements
- Owner payouts
- Owner portal

---

# 24. Audit Trail

All important mutations must create audit records.

Audit event fields:

- Organization
- User
- Action
- Entity type
- Entity ID
- Human-readable action name
- Old values
- New values
- Timestamp
- Request method
- Request path
- IP optional
- Correlation/request ID

Audit:

- Create
- Update
- Delete/archive
- Restore
- Lease activation
- Lease termination
- Payment creation
- Payment reversal
- Charge waiver
- Role changes
- Document deletion
- Settings changes

Audit logs must be immutable from normal application users.

---

# 25. Search

Global organization search should support:

- Tenant name
- Tenant phone
- Tenant email
- Property
- Unit
- Lease number
- Receipt number
- Payment reference
- Maintenance ticket

---

# 26. API Requirements

Backend should expose REST APIs.

Recommended API prefix:

`/api/v1/`

Example resources:

- `/auth/`
- `/organizations/`
- `/users/`
- `/properties/`
- `/units/`
- `/owners/`
- `/tenants/`
- `/leases/`
- `/charges/`
- `/payments/`
- `/expenses/`
- `/maintenance/`
- `/vendors/`
- `/inspections/`
- `/documents/`
- `/reports/`
- `/notifications/`
- `/audit-trail/`

Use:
- Pagination
- Filtering
- Ordering
- Search
- Consistent error responses
- OpenAPI schema

---

# 27. Recommended Backend Modules

Django apps:

```text
apps/
  accounts/
  organizations/
  properties/
  owners/
  tenants/
  leases/
  billing/
  maintenance/
  inspections/
  documents/
  notifications/
  reports/
  audit/
  subscriptions/
  common/
```

Do not create microservices.

Keep modules isolated enough to extract later if needed.

---

# 28. Recommended Data Layer

Use:

- PostgreSQL
- UUIDs for externally exposed identifiers
- Decimal for money
- Explicit currency field where relevant
- UTC timestamps in storage
- Organization timezone for display/business rules

Never use floating-point values for money.

---

# 29. Background Jobs

Use Celery + Redis for:

- Recurring rent charge generation
- Rent reminders
- Overdue notifications
- Lease expiry reminders
- Email
- Report generation
- File processing
- Scheduled maintenance tasks

All jobs must be idempotent.

---

# 30. Financial Integrity Requirements

Financial records require special care.

Rules:

1. Never hard-delete posted payments.
2. Use reversal transactions.
3. Never mutate historical charge values because a lease changed.
4. Preserve allocation history.
5. Use database transactions for payment allocation.
6. Prevent duplicate payment creation where possible.
7. Maintain audit records for financial changes.
8. Use `Decimal`.
9. Add unique business references where appropriate.

---

# 31. Security Requirements

Required:

- Organization data isolation
- Role-based permissions
- Object-level access where required
- Password hashing through framework defaults
- CSRF protection where applicable
- Rate limiting on authentication endpoints
- Input validation
- File type validation
- Secure file access
- Audit logging
- Environment-based secrets
- No secrets committed to Git
- Secure production cookies
- HTTPS in production

---

# 32. Non-Functional Requirements

## Performance

Target:
- Common API responses under 500 ms under normal load
- Dashboard under 2 seconds for normal-sized organizations
- Pagination for large datasets

## Reliability

- Database backups
- Restore procedure
- Error monitoring
- Structured logs
- Health endpoint

## Scalability

The MVP should comfortably support:

- Thousands of organizations
- Hundreds of properties per organization
- Thousands of units per organization
- Millions of ledger entries platform-wide

Optimize only after profiling.

---

# 33. Subscription/Billing Readiness

Do not require subscription billing to launch the first internal build.

Data model should support later:

- Plans
- Trial period
- Subscription status
- User limits
- Unit limits
- Feature flags

Never scatter plan checks throughout code. Use a centralized entitlements/service layer.

---

# 34. Future Marketplace Compatibility

Prepare for future marketplace support.

A unit/property should eventually be publishable externally.

Possible future fields:

- Public listing title
- Public description
- Listing price
- Public photos
- Amenities
- Availability date
- Marketplace status
- Listing slug
- Verification status

Do NOT build marketplace workflows in MVP.

---

# 35. MVP Definition

The first sellable version must contain:

- Authentication
- Organizations
- Roles/permissions
- Properties
- Units
- Tenants
- Leases
- Rent charges
- Payments
- Receipts
- Arrears
- Expenses
- Maintenance
- Documents
- Dashboard
- Core reports
- Audit trail
- Email/in-app notifications

If these work reliably, the product is sellable.

---

# 36. Phase 2

- Tenant portal
- Owner portal
- Inspections
- Vendor management enhancements
- SMS/WhatsApp
- Automated owner statements
- Mobile applications
- Advanced analytics
- Subscription billing
- Custom document templates
- Payment-provider integrations

---

# 37. Phase 3

- Dwella Marketplace
- Publish vacancy from management suite
- Applications
- Viewings
- Applicant screening
- Marketplace messaging
- Online payments
- AI-assisted workflows
- Regional/country configuration

---

# 38. Testing Requirements

Minimum:

- Unit tests for financial calculations
- Permission tests
- Organization isolation tests
- API tests
- Lease activation tests
- Recurring charge generation tests
- Payment allocation tests
- Payment reversal tests
- Arrears tests
- Audit-trail tests

Critical rule:

**A test must prove that a user from Organization A cannot retrieve or mutate Organization B data.**

---

# 39. Codex Implementation Instructions

Codex should:

1. Implement this as a modular monolith.
2. Use Django + Django REST Framework.
3. Use PostgreSQL.
4. Use Celery + Redis for background work.
5. Use environment variables for configuration.
6. Keep business logic in services/domain functions rather than bloated views.
7. Keep serializers/controllers thin.
8. Use explicit permission classes.
9. Implement organization scoping centrally.
10. Use database transactions for financial workflows.
11. Add tests alongside each module.
12. Maintain OpenAPI documentation.
13. Avoid speculative features not listed in the current phase.
14. Avoid microservices.
15. Avoid premature abstractions.
16. Prefer readable code over clever code.
17. Add migrations for every model change.
18. Add seed/factory data for local development.
19. Add Docker development setup.
20. Add linting, formatting, test, and migration-check commands suitable for CI.

---

# 40. Initial Definition of Done

The first implementation milestone is complete when a new organization can:

1. Register
2. Invite a staff user
3. Create a property
4. Create units
5. Create a tenant
6. Create and activate a lease
7. Automatically generate rent due
8. Record a partial/full payment
9. Generate a receipt
10. See the remaining balance
11. See arrears
12. Add an expense
13. Submit/manage a maintenance ticket
14. Upload a document
15. View dashboard metrics
16. Export a basic report
17. View the audit trail

That workflow should be built and tested end-to-end before expanding the product.
