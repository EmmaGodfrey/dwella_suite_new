# Dwella Marketplace Admin Panel

## 🎯 Overview

This document outlines the admin panel structure for **Dwella Marketplace** platform administration. This panel is exclusively for **Super Admins** who moderate the marketplace where tenants find properties and property listers post listings.

**Scope:** Dwella Marketplace only (excludes Dwella Suite organization features)

---

## 👤 Super Admin Role

**Role:** `admin`  
**Scope:** Entire Dwella Marketplace Platform  
**Access Level:** Full platform control  

**Core Responsibilities:**
- Platform-wide content moderation and oversight
- User account management (tenants & property listers)
- Listing approval and moderation
- Verification badge approval
- Payment transaction oversight
- System configuration and settings
- Platform analytics and reporting
- Reference data management (property types, locations, amenities)

---

## 📱 Admin Sidebar Navigation

```
┌──────────────────────────────────────────────┐
│        DWELLA MARKETPLACE ADMIN              │
│                                              │
│  [Super Admin Badge 🔴]                      │
├──────────────────────────────────────────────┤
│                                              │
│  📊 Dashboard                                │
│     └─ Platform Overview                     │
│                                              │
│  👥 Users                                    │
│     ├─ All Users                             │
│     ├─ Tenants                               │
│     ├─ Property Listers                      │
│     └─ Flagged Users                         │
│                                              │
│  🏠 Listings                                 │
│     ├─ All Listings                          │
│     ├─ Pending Approval [!]                  │
│     ├─ Active Listings                       │
│     ├─ Flagged Listings                      │
│     ├─ Archived                              │
│     └─ Listing Statistics                    │
│                                              │
│  📝 Applications                             │
│     ├─ All Applications                      │
│     ├─ By Status                             │
│     └─ Application Stats                     │
│                                              │
│  ✅ Verifications                            │
│     ├─ Pending Approvals [!]                 │
│     ├─ Approved                              │
│     ├─ Rejected                              │
│     ├─ Revoked                               │
│     ├─ Verification Plans                    │
│     └─ Verification Stats                    │
│                                              │
│  💰 Payments                                 │
│     ├─ All Transactions                      │
│     ├─ Verification Payments                 │
│     ├─ Platform Fees                         │
│     ├─ Refunds                               │
│     └─ Revenue Analytics                     │
│                                              │
│  🎨 Amenities                                │
│     ├─ All Amenities                         │
│     ├─ Categories                            │
│     └─ Add/Edit/Delete                       │
│                                              │
│  📍 Reference Data                           │
│     ├─ Property Types                        │
│     ├─ Provinces                             │
│     ├─ Districts                             │
│     └─ Constituencies                        │
│                                              │
│  🔔 Notifications                            │
│     ├─ Send Notification                     │
│     ├─ Templates                             │
│     ├─ Bulk Push                             │
│     └─ Notification History                  │
│                                              │
│  📊 Analytics                                │
│     ├─ Platform Metrics                      │
│     ├─ User Activity                         │
│     ├─ Listing Performance                   │
│     ├─ Application Trends                    │
│     └─ Revenue Reports                       │
│                                              │
│  ⚙️ Settings                                 │
│     ├─ Platform Settings                     │
│     ├─ Payment Configuration                 │
│     ├─ Email Settings                        │
│     ├─ SMS Settings                          │
│     └─ Cache Management                      │
│                                              │
│  📋 Reports                                  │
│     ├─ User Reports                          │
│     ├─ Listing Reports                       │
│     ├─ Financial Reports                     │
│     └─ Export Data                           │
│                                              │
│  🔍 Audit Logs                               │
│     ├─ Admin Actions                         │
│     ├─ User Actions                          │
│     └─ System Events                         │
│                                              │
└──────────────────────────────────────────────┘
```

**[!]** = Priority badge indicating items requiring admin attention

---

## 📄 Page Details

### 📊 Dashboard
**Purpose:** Platform health overview and quick actions

**Metrics Displayed:**
- Total users (tenants vs property listers breakdown)
- Active listings count
- Pending approvals (listings + verifications) with alert badges
- Monthly revenue
- User growth chart
- Geographic distribution map

**Widgets:**
- Recent activity feed (last 20 actions)
- Quick actions panel (approve/reject/flag)
- Flagged content count
- System health indicators

---

### 👥 Users
**Purpose:** Manage all platform users

**Features:**
- Searchable/filterable user list (by role, status, registration date)
- User detail modal showing:
  - Profile information
  - All listings (if property lister)
  - All applications (if tenant)
  - Payment history
  - Verification status
  - Activity timeline
  
**Actions:**
- Suspend user (with reason)
- Activate suspended user
- Delete user account (soft delete)
- Send direct message
- View communication history
- Flag for manual review

**Filters:**
- Role (tenant/property lister)
- Status (active/suspended/flagged)
- Verification status
- Registration date range
- Location

---

### 🏠 Listings
**Purpose:** Moderate and manage all property listings

**Views:**
1. **All Listings** - Complete listing table
2. **Pending Approval** ⚡ - Priority queue for moderation
3. **Active** - Currently live listings
4. **Flagged** - Reported by users
5. **Archived** - Removed listings

**Filters:**
- Status (pending, active, rejected, archived)
- Property type
- Location (province, district, constituency)
- Price range
- Date posted
- Verification status of lister

**Listing Detail View:**
- All property information
- Photo gallery
- Lister information
- Application count
- View history
- Flag history

**Actions:**
- ✅ Approve (publishes listing)
- ❌ Reject (with reason dropdown)
- 🚩 Flag for review
- 📦 Archive
- ✏️ Edit (admin override)
- 🗑️ Delete (soft delete)

**Approval Workflow:**
- Side-by-side view (listing info + actions)
- Quick checklist:
  - [ ] Photos are appropriate
  - [ ] Description is accurate  
  - [ ] Price is reasonable
  - [ ] Location is valid
  - [ ] No prohibited content
- Rejection reasons dropdown:
  - Inappropriate images
  - Misleading description
  - Duplicate listing
  - Incorrect pricing
  - Violates terms of service
  - Other (text input)
- Auto-notification to lister on decision

---

### 📝 Applications
**Purpose:** Oversight of tenant applications to listings

**Features:**
- View all applications across platform
- Filter by:
  - Status (pending, accepted, rejected, cancelled)
  - Listing
  - Tenant
  - Date range
- Application timeline view
- No direct admin actions (view only for monitoring)

**Use Cases:**
- Monitor suspicious activity patterns
- Dispute resolution
- Platform analytics

---

### ✅ Verifications
**Purpose:** Approve user verification badges

**Priority: Pending Queue** ⚡
- Document viewer (ID cards, proof of ownership)
- Side-by-side comparison tool
- Verification checklist:
  - [ ] ID document is clear and valid
  - [ ] Face matches photo
  - [ ] Proof of ownership provided (for listers)
  - [ ] Documents are not expired
  - [ ] No signs of tampering

**Actions:**
- ✅ Approve (assigns verification badge)
- ❌ Reject (with feedback message)
- 📄 Request additional documents
- ⏸️ Hold for manual review
- 🚫 Revoke existing verification

**Verification Plans Management:**
- View all verification plans (Basic, Premium)
- Edit pricing
- Edit features/benefits
- Enable/disable plans
- Set validity periods

**Stats:**
- Approval rate
- Average processing time
- Rejected reasons breakdown
- Revenue from verifications

---

### 💰 Payments
**Purpose:** Monitor all financial transactions

**Transaction List:**
- All verification badge purchases
- Payment details (amount, method, status)
- User information
- Timestamp

**Views:**
- All transactions
- Successful payments
- Failed payments
- Refunded payments
- Pending payments

**Analytics:**
- Revenue charts (daily, weekly, monthly)
- Payment method breakdown
- Popular verification plans
- Conversion rates
- Transaction success rate

**Actions:**
- View transaction details
- Issue refund (with reason)
- Export financial data (CSV, PDF)
- Generate invoice

---

### 🎨 Amenities
**Purpose:** Manage amenity options for listings

**Features:**
- CRUD operations for amenities
- Category management (Indoor, Outdoor, Security, etc.)
- Icon upload/selection
- Drag-and-drop reordering
- Usage statistics (how many listings use each amenity)

**Amenity Fields:**
- Name
- Category
- Icon
- Description
- Active/Inactive status

---

### 📍 Reference Data
**Purpose:** Manage location and property type data

**Sections:**

1. **Property Types**
   - Add/edit/delete property types
   - Set default amenities per type
   - Usage count

2. **Provinces**
   - Manage ZM provinces
   - Associated districts count

3. **Districts**  
   - Linked to provinces
   - Associated constituencies count

4. **Constituencies**
   - Linked to districts
   - Listing count per constituency

**Features:**
- Hierarchical view (Province → District → Constituency)
- Bulk import via CSV
- Export current data
- Search and filter

---

### 🔔 Notifications
**Purpose:** Platform-wide communication

**Features:**

1. **Send Notification**
   - Select audience:
     - All users
     - Tenants only
     - Property listers only
     - Verified users only
     - By location
   - Title and message
   - Channel selection (Push/Email/SMS/All)
   - Schedule or send immediately
   - Attach link (optional)

2. **Templates**
   - Pre-saved notification templates
   - Variables support ({user_name}, {listing_title}, etc.)
   - Category organization

3. **Notification History**
   - Past notifications sent
   - Delivery statistics
   - Open/click rates

---

### 📊 Analytics
**Purpose:** Platform insights and reporting

**Dashboards:**

1. **Platform Metrics**
   - User growth (new registrations over time)
   - Active users (DAU, MAU)
   - User type breakdown
   - Churn rate

2. **Listing Performance**
   - New listings per day/week/month
   - Approval rate
   - Average time to approval
   - Most popular property types
   - Price distribution
   - Geographic heatmap

3. **Application Trends**
   - Applications per day
   - Acceptance rate
   - Most viewed listings
   - Tenant engagement metrics

4. **Revenue Reports**
   - Verification revenue trends
   - Revenue by verification plan
   - Forecasting
   - Refund rate

5. **Geographic Insights**
   - Listings by location
   - Most active areas
   - Price by area analysis

---

### ⚙️ Settings
**Purpose:** Platform configuration

**Sections:**

1. **Platform Settings**
   - Site name and tagline
   - Contact information
   - Feature toggles (enable/disable features)
   - Maintenance mode
   - Registration settings

2. **Payment Configuration**
   - Payment gateway settings (Stripe/PayPal/etc.)
   - Currency settings
   - Commission rates
   - Payment processing fees
   - Refund policies

3. **Email Settings**
   - SMTP configuration
   - Email templates
   - Sender information
   - Test email functionality

4. **SMS Settings**
   - SMS provider configuration
   - SMS templates
   - Sender ID
   - Test SMS functionality

5. **Cache Management**
   - Clear application cache
   - Clear route cache
   - Clear config cache
   - Clear view cache
   - Optimize application

---

### 📋 Reports
**Purpose:** Generate and export data reports

**Report Types:**
- User reports (registrations, activity, demographics)
- Listing reports (by type, location, status)
- Financial reports (revenue, transactions, refunds)
- Verification reports (approval rates, revenue)
- Application reports (trends, conversion)

**Features:**
- Date range selection
- Filter options
- Export formats: CSV, PDF, Excel
- Schedule recurring reports (email delivery)
- Report templates

---

### 🔍 Audit Logs
**Purpose:** Track all actions for accountability

**Log Types:**

1. **Admin Actions**
   - Listing approvals/rejections
   - User suspensions
   - Verification approvals
   - Settings changes
   - Data modifications

2. **User Actions**
   - Login attempts
   - Listing submissions
   - Profile updates
   - Suspicious activities

3. **System Events**
   - Payment processing
   - Email/SMS delivery
   - API calls
   - Errors and exceptions

**Features:**
- Searchable by user, action type, date
- Filter by severity/type
- Export logs
- Retention policy settings

---

## 🔥 High Priority Workflows

### 1. Listing Approval Flow
**Entry:** Dashboard → Pending Listings (badge shows count)

**Process:**
1. Click on pending listing
2. Review side-by-side view
3. Check approval checklist
4. Click ✅ Approve or ❌ Reject
5. If rejecting, select reason from dropdown
6. Confirm action
7. System auto-notifies lister
8. Return to pending queue

**Time Target:** < 2 minutes per listing

---

### 2. Verification Approval Flow  
**Entry:** Dashboard → Pending Verifications (badge shows count)

**Process:**
1. Open verification request
2. View document viewer (ID, proof of ownership)
3. Verify checklist items
4. Options:
   - ✅ Approve → Badge assigned, user notified
   - ❌ Reject → Add feedback, user notified
   - 📄 Request more docs → Specify what's needed
   - ⏸️ Hold → Flag for senior review
5. Next verification loads automatically

**Time Target:** < 5 minutes per verification

---

### 3. User Moderation Flow
**Entry:** Flagged Users / User Reports

**Process:**
1. Review user profile and history
2. Check all listings/applications
3. Review flag reasons
4. Review communication history
5. Decision:
   - Warn user (send message)
   - Suspend temporarily (set duration + reason)
   - Suspend permanently
   - Dismiss flag (no action)
6. User is notified of decision
7. Log action in audit trail

---

### 4. Content Moderation (Flagged Listings)
**Entry:** Listings → Flagged

**Process:**
1. View flagged listing
2. See flag reasons from users
3. Review listing content
4. Actions:
   - Remove listing (if violates terms)
   - Edit listing (fix issues)
   - Dismiss flags (false reports)
   - Warn lister
   - Suspend lister (severe violations)
5. Notify both flagger and lister of outcome

---

## 🔐 Admin Permissions

| Feature | Super Admin |
|---------|-------------|
| **View Platform Dashboard** | ✅ |
| **Manage All Users** | ✅ |
| **Suspend/Delete Users** | ✅ |
| **View All Listings** | ✅ |
| **Approve/Reject Listings** | ✅ |
| **Edit Any Listing** | ✅ |
| **Delete Listings** | ✅ |
| **View All Applications** | ✅ |
| **Manage Verifications** | ✅ |
| **Approve/Reject Verifications** | ✅ |
| **Revoke Verifications** | ✅ |
| **View All Payments** | ✅ |
| **Issue Refunds** | ✅ |
| **Manage Amenities** | ✅ |
| **Manage Reference Data** | ✅ |
| **Send Platform Notifications** | ✅ |
| **View Platform Analytics** | ✅ |
| **Manage System Settings** | ✅ |
| **View Audit Logs** | ✅ |
| **Export Data** | ✅ |

---

## 🛠️ Technical Implementation

### Backend Routes
**Base Path:** `/api/v1/admin`  
**Middleware:** `['auth:sanctum', 'admin']`

**Key Route Groups:**
```php
Route::middleware(['auth:sanctum', 'admin'])->prefix('admin')->group(function () {
    // Dashboard
    Route::get('/dashboard/overview', [AdminDashboardController::class, 'overview']);
    
    // Users
    Route::get('/users', [AdminUserController::class, 'index']);
    Route::post('/users/{id}/suspend', [AdminUserController::class, 'suspend']);
    Route::post('/users/{id}/activate', [AdminUserController::class, 'activate']);
    
    // Listings
    Route::get('/listings', [AdminListingController::class, 'index']);
    Route::post('/listings/{id}/approve', [AdminListingController::class, 'approve']);
    Route::post('/listings/{id}/reject', [AdminListingController::class, 'reject']);
    Route::post('/listings/{id}/flag', [AdminListingController::class, 'flag']);
    
    // Verifications
    Route::get('/verifications', [AdminVerificationController::class, 'index']);
    Route::post('/verifications/{id}/approve', [AdminVerificationController::class, 'approve']);
    Route::post('/verifications/{id}/reject', [AdminVerificationController::class, 'reject']);
    Route::post('/verifications/{id}/revoke', [AdminVerificationController::class, 'revoke']);
    
    // Payments
    Route::get('/payments', [AdminPaymentController::class, 'index']);
    Route::get('/payments/analytics', [AdminPaymentController::class, 'analytics']);
    
    // Amenities
    Route::apiResource('amenities', AdminAmenityController::class);
    
    // Reference Data
    Route::prefix('reference-data')->group(/* routes */);
    
    // Notifications
    Route::post('/notifications/send', [AdminNotificationController::class, 'send']);
    
    // Settings
    Route::put('/settings', [AdminSettingsController::class, 'update']);
});
```

### Policies (AdminPolicy)
```php
public function viewAdmin($user): bool
{
    return $user->isAdmin();
}

public function moderateListing($user, $listing): bool
{
    return $user->isAdmin();
}

public function suspend User($user): bool
{
    return $user->isAdmin();
}
```

### Queries (Super Admin sees everything)
```php
// All users
$users = User::all();

// All listings
$listings = Listing::all();

// Pending listings
$pendingListings = Listing::where('status', 'pending')->get();

// Pending verifications
$pendingVerifications = VerificationRequest::where('status', 'pending')->get();
```

---

## 🎨 Frontend Structure

### Recommended Stack
- **Framework:** Vue 3 / React
- **UI Library:** Tailwind CSS + Shadcn/UI or Headless UI
- **Charts:** Chart.js or Recharts
- **Tables:** TanStack Table (React Table)
- **State Management:** Pinia (Vue) / Zustand (React)
- **API Client:** Axios

### Component Structure
```
src/
├── pages/
│   └── admin/
│       ├── Dashboard.vue
│       ├── users/
│       │   ├── UserList.vue
│       │   ├── UserDetail.vue
│       │   ├── SuspendDialog.vue
│       │   └── UserHistory.vue
│       ├── listings/
│       │   ├── ListingList.vue
│       │   ├── PendingQueue.vue
│       │   ├── ListingDetail.vue
│       │   ├── ApprovalView.vue
│       │   └── FlaggedListings.vue
│       ├── verifications/
│       │   ├── PendingQueue.vue
│       │   ├── DocumentViewer.vue
│       │   ├── ApprovalChecklist.vue
│       │   └── VerificationPlans.vue
│       ├── payments/
│       │   ├── TransactionList.vue
│       │   ├── PaymentDetail.vue
│       │   └── RevenueAnalytics.vue
│       ├── amenities/
│       │   ├── AmenityList.vue
│       │   └── AmenityForm.vue
│       ├── reference-data/
│       │   ├── PropertyTypes.vue
│       │   └── Locations.vue
│       ├── notifications/
│       │   ├── SendNotification.vue
│       │   └── NotificationHistory.vue
│       ├── analytics/
│       │   ├── PlatformMetrics.vue
│       │   └── Reports.vue
│       ├── settings/
│       │   └── Settings.vue
│       └── audit/
│           └── AuditLogs.vue
│
├── components/
│   └── admin/
│       ├── layout/
│       │   ├── AdminLayout.vue
│       │   ├── Sidebar.vue
│       │   └── Header.vue
│       ├── dashboard/
│       │   ├── StatCard.vue
│       │   ├── ActivityFeed.vue
│       │   ├── QuickActions.vue
│       │   └── ChartWidget.vue
│       └── shared/
│           ├── DataTable.vue
│           ├── StatusBadge.vue
│           ├── ActionMenu.vue
│           ├── ApprovalDialog.vue
│           ├── RejectDialog.vue
│           └── ConfirmDialog.vue
│
└── composables/
    ├── useAuth.js              // Check if admin
    ├── useAdminApi.js          // Admin API calls
    └── useNotifications.js     // Toast notifications
```

### Example Composables

```javascript
// composables/useAuth.js
export function useAuth() {
  const user = ref(null)
  
  const isAdmin = computed(() => {
    return user.value?.roles?.includes('admin')
  })
  
  const requireAdmin = () => {
    if (!isAdmin.value) {
      router.push('/unauthorized')
      throw new Error('Unauthorized')
    }
  }
  
  return { user, isAdmin, requireAdmin }
}

// composables/useAdminApi.js
export function useAdminApi() {
  const approveListing = async (listingId) => {
    return await api.post(`/admin/listings/${listingId}/approve`)
  }
  
  const rejectListing = async (listingId, reason) => {
    return await api.post(`/admin/listings/${listingId}/reject`, { reason })
  }
  
  const suspendUser = async (userId, reason, duration) => {
    return await api.post(`/admin/users/${userId}/suspend`, { reason, duration })
  }
  
  const approveVerification = async (verificationId) => {
    return await api.post(`/admin/verifications/${verificationId}/approve`)
  }
  
  return {
    approveListing,
    rejectListing,
    suspendUser,
    approveVerification
  }
}
```

---

## 📱 Mobile Responsiveness

### Priority for Mobile
- ✅ Dashboard overview
- ✅ Approve/reject listings (simplified view)
- ✅ Approve/reject verifications
- ✅ View user profiles
- ✅ Send notifications

### Desktop Only (Optional)
- Complex analytics charts
- Bulk operations
- Advanced settings
- Data exports

---

## 🚀 Implementation Phases

### Phase 1: Core Admin MVP ✅
- [x] Basic dashboard
- [x] User list and details
- [x] Listing moderation (approve/reject)
- [x] Payment overview
- [x] Basic analytics

### Phase 2: Verification System
- [ ] Verification approval workflow
- [ ] Document viewer
- [ ] Verification plans management
- [ ] Badge assignment system

### Phase 3: Enhanced Moderation
- [ ] Flagged content queue
- [ ] User suspension system
- [ ] Communication tools
- [ ] Bulk operations

### Phase 4: Analytics & Reporting
- [ ] Advanced analytics dashboards
- [ ] Custom report builder
- [ ] Scheduled reports
- [ ] Data export functionality

### Phase 5: Advanced Features
- [ ] Audit logs
- [ ] Activity timeline
- [ ] Automated moderation rules
- [ ] AI-powered fraud detection
- [ ] Geographic heatmaps

---

## 🎯 Key Principles

### ✅ DO:
- Prioritize pending approval queues (show count badges)
- Provide clear, easy approve/reject workflows
- Always require reasons for rejections
- Auto-notify users of admin actions
- Show comprehensive user history for context
- Implement search and filters on all lists
- Track ALL admin actions in audit logs
- Use confirmation dialogs for destructive actions
- Provide undo options where possible

### ❌ DON'T:
- Allow admin actions without confirmation
- Skip providing reasons for rejections/suspensions
- Forget to notify affected users
- Allow permanent deletion without archiving first
- Expose sensitive user data unnecessarily
- Make critical actions easy to trigger accidentally
- Forget to log admin actions

---

## 📚 Related Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - Overall backend architecture
- [routes/api.php](routes/api.php) - API routes
- [app/Domains/Admin/routes.php](app/Domains/Admin/routes.php) - Admin domain routes
- [database/seeders/RoleSeeder.php](database/seeders/RoleSeeder.php) - Role definitions
- [app/Domains/Admin/Policies/AdminPolicy.php](app/Domains/Admin/Policies/AdminPolicy.php) - Admin policies

---

## 🔄 Real-Time Features (Future)

Consider implementing:
- Real-time notification when new listings submitted
- Live chat with users for support
- Real-time dashboard metrics updates
- Collaborative moderation (multiple admins working)
- Activity presence indicators

**Tech Stack:** Laravel WebSockets / Pusher / Socket.io

---

**Last Updated:** March 2, 2026  
**Maintained By:** Dwella Development Team  
**Document Version:** 1.0
