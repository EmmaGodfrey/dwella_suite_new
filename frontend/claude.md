# Dwella Suite — Web App (Nuxt 3)

## What This App Is

One app serving both landlords/property managers (Suite) and platform admins.
Same login, same UI shell — navigation and page access are gated entirely by
permissions returned in `GET /auth/me`. No separate admin app needed.

Backend API: `https://api.dwella.zm/api/v1`

---

## Stack

- Nuxt 3
- Pinia (state)
- Tailwind CSS
- `$fetch` / `useFetch`

---

## Environment Variables

```env
NUXT_PUBLIC_API_URL=https://api.dwella.zm
```

---

## Auth Pattern

Token in cookie (SSR-safe). Every request sends `Authorization: Bearer <token>`.

```ts
// composables/useApi.ts
const token = useCookie('dwella_token')
return $fetch.create({
  baseURL: useRuntimeConfig().public.apiUrl,
  headers: computed(() => ({
    Authorization: token.value ? `Bearer ${token.value}` : '',
  })),
})
```

Global 402 handler — redirect to subscription page:
```ts
// plugins/api.ts
if (error.status === 402) navigateTo('/subscriptions/plans')
```

---

## The /auth/me Response (source of truth for all permissions)

```json
{
  "id": 1,
  "full_name": "Emma Godfrey",
  "email": "emma@dwella.zm",
  "phone": "0971234567",
  "is_admin": false,
  "is_lister": true,
  "system_roles": ["property_lister", "tenant"],
  "permissions": {
    "admin_access": false,
    "admin_user_read": false,              "admin_user_create": false,
    "admin_user_update": false,            "admin_user_delete": false,
    "admin_listing_read": false,           "admin_listing_approve": false,
    "admin_listing_reject": false,         "admin_listing_publish": false,
    "admin_listing_archive": false,        "admin_listing_delete": false,
    "admin_organization_read": false,      "admin_organization_create": false,
    "admin_organization_update": false,    "admin_organization_verify": false,
    "admin_organization_suspend": false,   "admin_organization_activate": false,
    "admin_organization_delete": false,
    "admin_application_read": false,
    "admin_verification_read": false,      "admin_verification_approve": false,
    "admin_verification_reject": false,    "admin_verification_revoke": false,
    "admin_verification_plan_read": false, "admin_verification_plan_create": false,
    "admin_verification_plan_update": false,"admin_verification_plan_delete": false,
    "admin_subscription_read": false,      "admin_subscription_cancel": false,
    "admin_subscription_reactivate": false,
    "admin_subscription_plan_read": false, "admin_subscription_plan_create": false,
    "admin_subscription_plan_update": false,"admin_subscription_plan_delete": false,
    "admin_payment_read": false,
    "admin_ref_data_read": false,          "admin_ref_data_create": false,
    "admin_ref_data_update": false,        "admin_ref_data_delete": false,
    "admin_amenity_read": false,           "admin_amenity_create": false,
    "admin_amenity_update": false,         "admin_amenity_delete": false,
    "admin_setting_read": false,           "admin_setting_update": false,
    "admin_notification_read": false,      "admin_notification_send": false
  },
  "organizations": [
    {
      "id": 1,
      "name": "Godfrey Properties",
      "type": "agency",
      "is_verified": true,
      "org_role": "owner",
      "status": "active",
      "has_subscription": true,
      "permissions": {
        "listing_read": true,    "listing_create": true,   "listing_update": true,
        "listing_submit": true,  "listing_delete": false,  "listing_publish": false,  "listing_archive": false,
        "application_read": true, "application_update_status": true,
        "lease_read": true,      "lease_create": true,     "lease_update": true,
        "lease_renew": true,     "lease_terminate": true,
        "maintenance_read": true, "maintenance_create": true, "maintenance_update": true,
        "team_read": true,       "team_create": true,      "team_update": true,  "team_delete": true,
        "subscription_read": true, "subscription_create": true,
        "subscription_upgrade": true, "subscription_cancel": true,
        "organization_read": true, "organization_update": true, "organization_delete": true
      }
    }
  ]
}
```

Fetch on login and on every page refresh. Store in Pinia.
The backend pre-computes all flags via `PermissionsMatrix` — no local role derivation needed.

---

## Pinia Stores

```ts
// stores/auth.ts
{
  user: User | null         // full /auth/me response
  token: string | null
  activeOrg: Org | null     // org currently being managed
  orgs: Org[]               // computed from user.organizations

  isAdmin: computed         // user.is_admin
  isLister: computed        // user.is_lister

  login(email, password): Promise<void>
  logout(): void
  fetchMe(): Promise<void>
  setActiveOrg(org): void
}
```

---

## Permission Composable

```ts
// composables/usePermissions.ts
export const usePermissions = () => {
  const auth = useAuthStore()

  // System-level flags (admin_* keys) live on user.permissions
  const sys = computed(() => auth.user?.permissions ?? {})

  // Org-scoped flags live on the active org's permissions object
  const org = computed(() => auth.activeOrg?.permissions ?? {})

  // Check any permission by its exact key
  const can = (key: string): boolean =>
    org.value[key] ?? sys.value[key] ?? false

  return {
    isAdmin:         computed(() => auth.user?.is_admin ?? false),
    hasSubscription: computed(() => auth.activeOrg?.has_subscription ?? false),
    can,
  }
}
```

Usage:
```ts
const { can } = usePermissions()

can('listing_create')            // show Create Listing button
can('admin_listing_approve')     // show Approve button in admin panel
can('team_delete')               // show Remove Member button
can('subscription_cancel')       // show Cancel Subscription button
can('admin_access')              // show admin nav section
```

---

## Middleware

```ts
// middleware/auth.ts   — redirect /auth/login if no token
// middleware/org.ts    — redirect /organizations if activeOrg is null (suite pages)
// middleware/admin.ts  — redirect /dashboard if !can('admin_access') (admin/* pages)
```

---

## Navigation (visibility by permission)

```
Dashboard              always visible (any authenticated org member)
Listings               can('listing_read')
Applications           can('application_read')
Leases                 can('lease_read')
Maintenance            can('maintenance_read')
──────────────────────────────────────────────
Team                   can('team_read')
Subscription           can('subscription_read')
──────────────────────────────────────────────
ADMIN SECTION          can('admin_access')
  Overview
  Users
  Listings (moderate)
  Organizations
  Applications
  Verifications
  Subscriptions
  Payments
  Settings
```

---

## Pages & API Calls

### Auth

#### `/auth/login`
```
POST /auth/login
Body: { email, password }
→ GET /auth/me  (eager-loaded roles + orgs + permissions)
→ store in Pinia
→ if organizations is empty → redirect /organizations/create
→ else redirect /dashboard
```

#### `/auth/register`
```
POST /auth/register
Body: { full_name, email, password, password_confirmation, phone }
→ GET /auth/me
→ redirect /organizations/create
```

#### `/auth/forgot-password`
```
POST /auth/forgot-password
Body: { email }
```

#### `/auth/reset-password`
Reads `?token=&email=` from URL query string.
```
POST /auth/reset-password
Body: { token, email, password, password_confirmation }
```

---

### Dashboard

#### `/dashboard`
```
GET /listings/mine?organization_id=:orgId
GET /maintenance/tickets?organization_id=:orgId&status=open
GET /leases
GET /subscriptions/current?organization_id=:orgId
```

---

### Organizations

#### `/organizations` — Org picker / switcher
```
(data from Pinia — no API call needed)
setActiveOrg(org) → redirect /dashboard
```

#### `/organizations/create`
```
POST /organizations
Body: { name, type, email, phone, address }

POST /users/become-lister        (once — grants property_lister system role)

GET /auth/me                     (refresh Pinia)
→ redirect /subscriptions/plans if !has_subscription, else /dashboard
```

#### `/organizations/[id]` — Org settings — `can('organization_update')`
```
GET /organizations/:id
PUT /organizations/:id
Body: { name, email, phone, address }
```

#### `/organizations/[id]/members` — Team — `can('team_read')`
```
GET    /organizations/:id/members

POST   /organizations/:id/members          — requires can('team_create')
Body:  { email, org_role }                 // org_role: manager | member

PUT    /organizations/:id/members/:memberId   — requires can('team_update')
Body:  { org_role }

DELETE /organizations/:id/members/:memberId   — requires can('team_delete')
```

---

### Subscriptions — `can('subscription_read')`

#### `/subscriptions/plans` — Browse plans
```
GET /subscriptions/plans
```

#### `/subscriptions/subscribe` — Subscribe / upgrade — `can('subscription_create')`
```
POST /subscriptions/subscribe
Body: { organization_id, plan_id, billing_period }   // billing_period: monthly | yearly

POST /payments/lenco/mobile-money
Body: {
  amount_minor,
  phone,
  payment_type: "subscription",
  payable_id,        // subscription ID
  payable_type: "subscription_plan"
}

GET /payments/lenco/verify?reference=:ref   ← poll every 3s until status=successful
```

#### `/subscriptions` — Current subscription
```
GET  /subscriptions/current?organization_id=:orgId

POST /subscriptions/cancel    Body: { organization_id }   — requires can('subscription_cancel')
POST /subscriptions/upgrade   Body: { organization_id, plan_id, billing_period }   — requires can('subscription_upgrade')
```

---

### Listings — `can('listing_read')`

#### `/listings` — My listings
```
GET /listings/mine?organization_id=:orgId
```

#### `/listings/create` — `can('listing_create')`

Load reference data:
```
GET /listings/property-types
GET /listings/locations/provinces
GET /listings/locations/districts?province_id=:id
GET /listings/locations/wards?district_id=:id
GET /listings/amenities
```

AI helpers (optional):
```
POST /ai/price-suggest
Body: { property_type_id, province_id, district_id, amenities_count }

POST /ai/generate-description
Body: { property_type, location, price_zmw, period, amenities }
```

Create:
```
POST /listings
Body: {
  organization_id, title, description, property_type_id,
  price_amount_minor, price_period, province_id, district_id,
  constituency_id, address_line, location_text,
  latitude, longitude, amenity_ids[]
}

POST /listings/:id/images        (multipart, field: images[], optional: thumbnail_index)
POST /listings/:id/submit
```

#### `/listings/[id]/edit` — `can('listing_update')`
```
GET    /listings/:id
PUT    /listings/:id             (same body as create, minus organization_id)
POST   /listings/:id/images      (multipart)
DELETE /listings/:id/images/:imageId
POST   /listings/:id/images/:imageId/thumbnail
```

#### `/listings/[id]/applications` — `can('application_read')`
```
GET /applications/for-listing/:listingId

PATCH /applications/:id/status                — requires can('application_update_status')
Body: { status }   // contacted | accepted | declined
```

---

### Leases — `can('lease_read')`

#### `/leases`
```
GET /leases
```

#### `/leases/create` — `can('lease_create')`
```
GET  /listings/mine?organization_id=:orgId      (pick property)

POST /leases
Body: {
  property_id,
  tenant_id,
  start_date,                // YYYY-MM-DD
  end_date,                  // YYYY-MM-DD
  monthly_rent,              // integer minor units (ngwee)
  security_deposit           // integer minor units (ngwee), nullable
}
```

#### `/leases/[id]`
```
GET  /leases/:id

POST /leases/:id/renew       — requires can('lease_renew')
Body: { months }             // 1–24

POST /leases/:id/terminate   — requires can('lease_terminate')
```

---

### Maintenance — `can('maintenance_read')`

#### `/maintenance`
```
GET /maintenance/tickets?organization_id=:orgId
GET /maintenance/tickets?organization_id=:orgId&status=open
```

#### `/maintenance/create` — `can('maintenance_create')`
```
GET  /listings/mine?organization_id=:orgId      (pick property)

POST /maintenance/tickets
Body: { listing_id, title, description, priority }   // priority: low | medium | high
```

#### `/maintenance/[id]`
```
GET /maintenance/tickets/:id

PATCH /maintenance/tickets/:id                  — requires can('maintenance_update')
Body: { status, priority }
// status: open | in_progress | resolved | closed
```

---

### Notifications

#### `/notifications`
```
GET  /notifications
GET  /notifications/unread-count
PUT  /notifications/:id/read
POST /notifications/mark-all-read
```

---

### Account

#### `/account/profile`
```
GET /users/me
PUT /users/me
Body: { full_name, email, phone }
```

---

## Admin Pages — `can('admin_access')`

### `/admin` — Dashboard
```
GET /admin/dashboard/overview
GET /admin/dashboard/activities
GET /admin/dashboard/revenue-trends
GET /admin/dashboard/listings-trends
```

### `/admin/users` — `can('admin_user_read')`
```
GET    /admin/users

POST   /admin/users                                  — can('admin_user_create')
Body:  { full_name, email, password, phone, role }

PUT    /admin/users/:id                              — can('admin_user_update')
Body:  { full_name, email, phone, role }

DELETE /admin/users/:id                              — can('admin_user_delete')
```

### `/admin/listings` — Moderation queue — `can('admin_listing_read')`
```
GET  /admin/listings?status=pending
GET  /admin/listings?status=:status     // draft | pending | approved | published | rejected | archived
GET  /admin/listings/statistics
GET  /admin/listings/:id

POST /admin/listings                                 — can('admin_listing_create') [direct admin create]
POST /admin/listings/:id/approve                     — can('admin_listing_approve')
POST /admin/listings/:id/reject    Body: { reason }  — can('admin_listing_reject')
POST /admin/listings/:id/publish                     — can('admin_listing_publish')
POST /admin/listings/:id/archive                     — can('admin_listing_archive')
DELETE /admin/listings/:id                           — can('admin_listing_delete')
```

### `/admin/applications` — `can('admin_application_read')`
```
GET /admin/applications
GET /admin/applications/statistics
GET /admin/applications/:id
```

### `/admin/organizations` — `can('admin_organization_read')`
```
GET  /admin/organizations
GET  /admin/organizations/statistics
GET  /admin/organizations/:id

POST /admin/organizations                            — can('admin_organization_create')
Body: { name, type, email, phone, address }

PUT  /admin/organizations/:id                        — can('admin_organization_update')
Body: { name, type, email, phone, address }

POST /admin/organizations/:id/verify                 — can('admin_organization_verify')
POST /admin/organizations/:id/suspend                — can('admin_organization_suspend')
POST /admin/organizations/:id/activate               — can('admin_organization_activate')
DELETE /admin/organizations/:id                      — can('admin_organization_delete')
```

### `/admin/verifications` — `can('admin_verification_read')`
```
GET  /admin/verifications
GET  /admin/verifications/statistics
GET  /admin/verifications/:id

POST /admin/verifications/:id/approve                — can('admin_verification_approve')
POST /admin/verifications/:id/reject  Body: { reason } — can('admin_verification_reject')
POST /admin/verifications/:id/revoke  Body: { reason } — can('admin_verification_revoke')
```

Verification plans — `can('admin_verification_plan_read')`:
```
GET    /admin/verifications/plans
POST   /admin/verifications/plans       Body: { name, price_minor, ... }   — can('admin_verification_plan_create')
PUT    /admin/verifications/plans/:id                                       — can('admin_verification_plan_update')
DELETE /admin/verifications/plans/:id                                       — can('admin_verification_plan_delete')
```

### `/admin/subscriptions` — `can('admin_subscription_read')`
```
GET  /admin/subscriptions
GET  /admin/subscriptions/statistics
GET  /admin/subscriptions/:id

POST /admin/subscriptions/:id/cancel       — can('admin_subscription_cancel')
POST /admin/subscriptions/:id/reactivate   — can('admin_subscription_reactivate')
```

Subscription plans — `can('admin_subscription_plan_read')`:
```
GET    /admin/subscriptions/plans
POST   /admin/subscriptions/plans       Body: { name, price_minor, billing_period, ... }  — can('admin_subscription_plan_create')
PUT    /admin/subscriptions/plans/:id                                                      — can('admin_subscription_plan_update')
DELETE /admin/subscriptions/plans/:id                                                      — can('admin_subscription_plan_delete')
```

### `/admin/payments` — `can('admin_payment_read')`
```
GET /admin/payments
GET /admin/payments/statistics
GET /admin/payments/analytics?from=&to=&group_by=day|week|month|year
GET /admin/payments/:id
```

### `/admin/settings` — `can('admin_setting_read')`

#### Reference Data — `can('admin_ref_data_read')`
```
GET    /admin/reference-data/property-types
POST   /admin/reference-data/property-types     Body: { name, description }
PUT    /admin/reference-data/property-types/:id
DELETE /admin/reference-data/property-types/:id

GET    /admin/reference-data/provinces
POST   /admin/reference-data/provinces          Body: { name }
PUT    /admin/reference-data/provinces/:id
DELETE /admin/reference-data/provinces/:id

GET    /admin/reference-data/districts
POST   /admin/reference-data/districts          Body: { name, province_id }
PUT    /admin/reference-data/districts/:id
DELETE /admin/reference-data/districts/:id

GET    /admin/reference-data/constituencies
POST   /admin/reference-data/constituencies     Body: { name, district_id }
PUT    /admin/reference-data/constituencies/:id
DELETE /admin/reference-data/constituencies/:id
```

#### Amenities — `can('admin_amenity_read')`
```
GET    /admin/amenities
POST   /admin/amenities          Body: { name, category_id, icon }
PUT    /admin/amenities/:id
DELETE /admin/amenities/:id

GET    /admin/amenities/categories
POST   /admin/amenities/categories          Body: { name }
PUT    /admin/amenities/categories/:id
DELETE /admin/amenities/categories/:id
```

#### Payment Settings — `can('admin_setting_read')`
```
GET  /admin/settings/payment
PUT  /admin/settings/payment    Body: { ... }   — can('admin_setting_update')
POST /admin/settings/cache/clear               — can('admin_setting_update')
POST /admin/settings/email/test Body: { email } — can('admin_setting_update')
```

#### Notifications — `can('admin_notification_read')`
```
GET  /admin/notifications
GET  /admin/notifications/statistics
GET  /admin/notifications/templates

POST /admin/notifications/bulk-push            — can('admin_notification_send')
Body: { title, message, user_ids[], send_to_all }
```

---

## Enums & Values

| Field | Values |
|---|---|
| org_role | `owner` `manager` `member` |
| org status (pivot) | `active` `invited` `removed` |
| org type | `agency` `landlord` |
| listing status | `draft` `pending` `approved` `published` `rejected` `archived` |
| application status | `new` `contacted` `accepted` `declined` |
| maintenance status | `open` `in_progress` `resolved` `closed` |
| maintenance priority | `low` `medium` `high` |
| lease status | `active` `expired` `terminated` |
| subscription status | `active` `past_due` `cancelled` `expired` |
| billing_period | `monthly` `yearly` |
| price_period | `monthly` `weekly` `nightly` |

---

## What This App Does NOT Do

- No public listing browsing (that's Marketplace)
- No tenant-side application flow (apply for a property)
- No verification badge purchase (that's Marketplace)
- No saved searches or AI semantic search
- No device/push token registration (web app — no push support)

---

## Endpoints This App Never Calls

```
GET  /listings                        (public browse — Marketplace only)
GET  /search/listings                 (Marketplace search)
POST /ai/search                       (semantic search — Marketplace only)
GET  /search/saved                    (Marketplace saved searches)
POST /search/saved
PUT  /search/saved/:id
DELETE /search/saved/:id
POST /applications                    (apply as tenant — Marketplace only)
GET  /applications/mine               (tenant view — Marketplace only)
GET  /verification/status/:type/:id   (Marketplace only)
POST /verification/request            (Marketplace only)
POST /users/device-token              (mobile only)
DELETE /users/device-token            (mobile only)
```
