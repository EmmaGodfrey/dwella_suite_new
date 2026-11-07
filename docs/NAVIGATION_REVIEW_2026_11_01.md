# Module navigation review — 1 November 2026

The strongest candidates for expandable module navigation are Billing, Maintenance, Reports, Outreach and platform Transactions. Messages also has two distinct views worth exposing. Settings needs clearer section navigation, particularly for the eight-section admin screen.

The user approved this hierarchy on 1 November 2026. The implementation is local; this document does not indicate that it has been deployed. The review tables below record the starting point and the agreed decisions.

## Implementation

- Added expandable Billing, Reports, Maintenance and Messages sections, plus platform Transactions and Outreach. Module labels open the default screen; separate buttons expand the children. The active section opens automatically.
- Added click/keyboard menus for collapsed desktop navigation. Mobile expansion keeps navigation open; selecting a destination closes it. Links retain browser modifier behavior and use the existing deployment-prefix helper.
- Reports (`?report=`), Messages (`?view=`) and the existing Vendors drawer (`?panel=vendors`) now support direct links and reloads. Removed the Receipts/Payouts and Vendors toolbar navigation buttons. Existing task buttons and screen layouts remain.
- Selection uses path boundaries and query state; breadcrumbs identify the active child. Transactions reset section-specific filter state when changing resource.
- Settings uses a vertical section list on desktop and a section selector on mobile, preserving `?tab=` links. The manager's Billing setting is labelled Payments (receiving account, how tenants pay you and billing defaults).
- Tenant navigation stays flat. Payouts/Vendors keep their management-capability visibility gates; portfolio modules still require an admin support workspace. No backend or payment-processing changes are part of this implementation.
- Added seven navigation-state regression tests. All 32 frontend Node tests (including the seven new tests) and the production build passed. Browser validation with synthetic API fixtures passed manager/admin/tenant navigation, direct reloads, Back/Forward, Vendors, collapsed keyboard/focus behavior, mobile expansion/selection, both themes, reduced motion, Settings sections and `/test/`-prefixed links. Modified clicks retain the browser default and leave the current tab in place. This validates navigation, not live gateway transactions. The build still reports the existing bundle-size warning.
- An editable Billing navigation reference reuses the existing Dwella components in the [product design file](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=291-4726).

## Property manager modules

| Module | Recommendation | Children / treatment | Current implementation and work needed |
| --- | --- | --- | --- |
| Dashboard | Keep one destination | Dashboard | Widgets already link to the relevant records. They do not need sidebar children. |
| Get started | Keep one destination | Setup steps stay inside the setup flow | Onboarding is a sequential task. Preserve its existing step navigation. |
| Billing | High-priority submenu | Invoices; Receipts; Payouts | All three screens already exist. `/billing` is the invoice list; `/billing/receipts` and `/billing/payouts` are reached through buttons in the invoice toolbar. Expose these as destinations and leave task buttons for Generate invoices/New charge. |
| Maintenance | High-priority submenu | Requests; Vendors | Vendors is currently a drawer reached through a button. Give it a direct, shareable navigation state while retaining the existing drawer. Board/List stays a view toggle within Requests. |
| Reports | Submenu | Rent roll; Arrears | These are the two currently rendered reports. Selection is component state, so add a URL-backed selection before linking children. Additional reports must wait for their actual screens; do not create dead navigation from backend endpoints alone. |
| Messages | Submenu for the distinct views in current develop | Operational updates; Notices & reminders | Current develop switches between different histories through a Message type dropdown backed by local state. Give each a URL-backed selection. Compose/New message stays an action. Channel and delivery status stay filters. This view split may not yet be deployed. |
| Properties | Keep current navigation initially | Properties; units remain inside the selected property | There is no independent portfolio-wide Units screen today. A future Units child could be valuable, but it needs a real screen rather than a link that opens an arbitrary property's units. Keep Import units/Add property as actions. |
| Tenants | Keep one destination | Status/archive filters and tenant detail stay on the screen | Active, Applicant, Past and Archived describe the same records. Inviting/editing a tenant remains contextual. Do not multiply sidebar items for every filter. |
| Leases | Keep one destination | Lease status filters; documents, signing and deposit actions inside lease detail | The existing list/detail relationship is useful. There is no separate global signing/document workspace to expose as a child. |
| Settings | Improve section navigation | Account; Workspace; Receiving account; Notifications; Security | Five sections currently appear as horizontal tabs. Rename the section currently called Billing to Receiving account so it is not confused with the Billing module. Prefer a local section list on wide screens and a compact section selector on mobile. |

The Payouts page already includes the balance, withdrawal action/history and receiving-account access. It does not need another layer of sidebar nesting for those individual controls. Keep Withdraw as a button inside Payouts. Keep the existing receiving-account setting accessible from that context and Settings rather than creating competing destinations for the same configuration.

### Proposed manager sidebar

```text
Overview
  Dashboard
  Get started
  Reports
    Rent roll
    Arrears

Portfolio
  Properties
  Tenants
  Leases

Operations
  Billing
    Invoices
    Receipts
    Payouts
  Maintenance
    Requests
    Vendors
  Messages
    Operational updates
    Notices & reminders

Settings → its role-specific section navigation
```

Only expand the active module automatically; permit users to open another group deliberately. A module's default page remains reachable with its label, with a separate chevron to expand/collapse its children. Use only one child level. Individual invoice, tenant, repair and lease records belong in breadcrumbs and contextual views.

## Super admin modules

| Module | Recommendation | Children / treatment |
| --- | --- | --- |
| Transactions | High-priority submenu | Collections; Withdrawals; Automatic payouts; Gateway ledger. These views already have direct `?view=` selections. Keep automatic-payout history accessible for older records even when new automatic payouts are disabled. |
| Outreach | High-priority submenu | Contacts; Sequences; Review queue; Outbox. All four already have routes and page-level navigation. Put configuration in the existing Settings → Outreach section, with a contextual link if needed. |
| Messages | Same two history destinations as current develop | Operational updates; Notices & reminders. Respect the admin's existing read/send capabilities; do not expose manager composition merely because the navigation is shared. |
| Settings | Local section navigation | Account; Security; Payments; Messaging; Outreach; Assistant; Support; Beta. Eight sections are crowded in a horizontal strip. Avoid expanding eight items out of a fixed sidebar footer where they can be clipped. |
| Administration overview | Keep one destination | Overview metrics and shortcuts remain on the dashboard. |
| Workspaces | Keep one destination | Workspace detail and support-session entry stay contextual. |
| Users | Keep one destination | Account detail and access actions stay contextual. |
| Identity checks | Keep one destination | Review status is a filter; a document review is a record detail. |
| Beta signups | Keep one destination | Applicant states stay filters; invitation/contact actions stay contextual. |
| Audit log | Keep one destination | Actor/workspace/action filters stay within the log. |
| Workspace support navigation | Preserve the existing separate context | Show portfolio modules only during an active support session, and apply their existing capabilities. Platform Transactions and workspace Payouts are different destinations and must remain distinct. |

## Tenant navigation

Keep Home, My lease, Payments, Maintenance and Settings simple. Tenant Payments already combines invoices and receipt history; do not expose manager Payouts or a receiving-account section. Lease documents stay under My lease, and repairs stay under Maintenance. Settings has Account, Notifications and Security sections.

## Route and interaction requirements

- Reuse Fluent UI navigation components already installed (`NavCategory`, `NavCategoryItem`, `NavSubItem`, `NavSubItemGroup`/appropriate split navigation). No new navigation library is needed.
- Billing's existing paths remain canonical. Report and Messages children require URL-backed state; Vendors needs a query/panel state that opens the existing drawer on direct load. These are new navigation states, not existing routes to advertise prematurely.
- Settings already has `?tab=` selection; Transactions already has `?view=` selection; Outreach already has individual routes. Preserve those links and legacy redirects.
- Selection must match both the path and relevant query state. The current first-prefix match would otherwise select Billing instead of Payouts, or select the wrong Settings/Transactions child. Use path-segment boundaries and the most specific match.
- Add accurate child titles and breadcrumbs. Payouts currently inherits the generic Billing section in the shared breadcrumb logic; it needs its own child crumb. Avoid duplicate Receipts crumbs when reorganizing routes.
- Keep anchors as real links, including new-tab/modifier clicks and the `/test/` deployment prefix. Preserve Back/Forward, refresh and existing contextual links from notifications, tours and dashboards.
- Expanded groups belong in the scrollable navigation region. In collapsed desktop navigation, expose children in an accessible click/keyboard flyout; in the mobile drawer use inline expansion. Expanding a category must not close the mobile drawer; selecting a destination should.
- Auto-expand the current module on direct loads and highlight the current child, including record-detail paths. Keep focus visible and provide labels/expanded state through the existing component primitives.
- Preserve existing role/capability restrictions, suspended/removed access handling and support-session boundaries. Navigation visibility does not replace backend authorization. Payouts and Vendors must retain their current capability gates.
- Keep actions as actions: Withdraw, New charge, Generate invoices, Add tenant, Add property, Import, New lease and Compose do not become navigation children.
- Do not fetch every child's data when opening a menu. Build the menu from existing user/access metadata and load a screen's data when visiting it.

## Suggested sequence

1. Design the expanded/collapsed/mobile sidebar treatment in the existing Dwella Figma file, preserving the current layouts and drawer conventions.
2. Start with Billing, admin Transactions and Outreach: their independent destinations already exist. Include selected-state, breadcrumbs and role checks.
3. Add URL-backed Requests/Vendors, report selection and message-history selection. Preserve current screen contents and forms.
4. Improve role-specific Settings section navigation separately. Leave Properties/Tenants/Leases and tenant navigation simple initially.

Validation covers direct links, refresh/history, selected children, access visibility, keyboard/flyout focus, mobile drawer behavior and both themes, plus the frontend production build. Backend changes from concurrent billing work are outside this navigation change.

## Source references

- Sidebar structure and role filtering: `frontend/src/shared/navigation.jsx`, `frontend/src/shared/components/AppSideNav.jsx`.
- Routes and breadcrumbs: `frontend/src/Route/Routes.jsx`, `frontend/src/shared/components/AppBreadcrumbs.jsx`.
- Hidden Billing destinations: `frontend/src/Components/Billing/index.jsx:144`.
- Vendors drawer entry: `frontend/src/Components/Maintenance/index.jsx:228`.
- Local report selection: `frontend/src/Components/Reports/index.jsx:13`.
- Message-history selector: `frontend/src/Components/Messages/index.jsx`.
- Settings sections: `frontend/src/Components/Settings/index.jsx:617`.
- Platform transaction sections: `frontend/src/Components/Platform/Transactions.jsx:514`.
- Outreach links: `frontend/src/Components/Outreach/OutreachUI.jsx:40`.
