# White surfaces and overlay review

Date: 24 October 2026. Status: **Corrected readability designs approved and implemented locally**. Page structures preserved; no backend changes, commit, push or deployment.

## User correction: preserve page structure

On 24 October the user rejected changes to page structure, especially Maintenance. This instruction supersedes the initial composition proposals recorded below. Preserve existing page headers and action locations, toolbar order, summary placement, directory/detail splits, board/list views and section order. Restrict this pass to surface colors, contrast, spacing, text hierarchy and form sizing. Appropriate short-task modal proposals remain subject to review.

The Figma proposals were corrected in place, retaining their links. Maintenance again has its header actions, compact toolbar/search/summary, four lanes (New, Scheduled, In progress, Done this week), original request cards and per-lane empty states. White lane backgrounds and stronger card/text separation improve readability. It no longer replaces the empty board with one centered empty message. On mobile, lanes retain the existing stacked behavior. Unsupported per-lane Add icons inherited from the old reference were removed.

The user subsequently approved these corrected designs for implementation. The implementation and checks at the end of this document supersede the earlier proposal-only status and validation notes.

Identity retains separate summary, filters and results. Directory/report proposals were restored from their original frame compositions and receive surface styling in place; the additional enclosing work-surface hierarchy was removed. Properties retains its directory/detail split. The generic new directory composition is hidden and marked SUPERSEDED. The review introduction now explicitly says to preserve page structure. Historical wording below describing unified workspaces is superseded by this correction.

[Open the reference set](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-1711). Page: **Review — Surfaces & overlays · 24 Oct**. The introduction records approval and implementation; the withdrawn generic directory composition is hidden. The approved short-task modals qualify the earlier drawers-first preference. Existing accepted source designs remain intact.

## Findings

- Record payment uses the shared 560px drawer and two-column grid. Fluent Dropdown has a 250px minimum width; after drawer padding and grid gap, a paired column has less room. The newer `.dwella-form-body` shrink overrides do not apply to this legacy drawer. Widening alone would also leave the mismatch on narrower screens. Proposed fix: a 640px focused modal, shrinking controls and container-based single-column reflow. Do not hide horizontal overflow to conceal a sizing defect.
- Maintenance renders its default empty board as four short grey columns with “Nothing here”. The background consequently dominates. Keep the same toolbar and four-column board, using white lane surfaces, clearer headers/counts and improved contrast. Preserve per-lane empty states when the board is empty.
- Identity checks renders its summary, filters and the empty-state branch outside its white table card. Add white surface treatments to these existing sections without merging or rearranging them. Summary counts must remain the summary endpoint's totals, independent of queue filters.
- `ChargeDrawer` also pairs Fluent dropdowns in the legacy drawer. Its repeatable invoice-line editor makes a drawer appropriate, with more width and a stacked line layout at narrow sizes.
- Other directories generally have white populated tables but inconsistent treatment for filters, loading and failures. Improve their existing surfaces while preserving the current section structure.

## Review links

| Proposal | Figma node |
| --- | --- |
| Payment modal, desktop | [170:1151](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-1151) |
| Payment validation / dark / mobile | [Validation](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-1295), [dark](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-1438), [mobile](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-1645) |
| Maintenance empty / board / filtered list / mobile | [Empty](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-106), [board](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-233), [filtered](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-367), [mobile](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-488) |
| Identity empty / populated / error / loading / mobile | [Empty](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-550), [populated](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-729), [error](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-936), [loading](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=172-2556), [mobile](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=170-1098) |
| Short admin modals | [Edit profile](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=171-826), [membership](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=171-965), [ownership](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=171-1099), [support reason](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=171-1244), [identity decision](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=171-1388), [new sequence](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=171-1508) |
| New charge drawer | [171:1643](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=171-1643) |

## Route coverage and design disposition

The source inventory reads 115 JSX/JS/SCSS files under `frontend/src`, including 25 files referencing overlays and ten referencing the shared EmptyState. Routing, navigation, shared styles and the page/form components inform this review. This is a frontend source/design audit; it is not a fresh live-browser regression run or a backend review. Existing 23 October screenshots and audit provide historical context only.

New proposal IDs below belong to the new review page. Retained references stay on their original Figma pages; retaining a layout means it already has appropriate surfaces, rather than claiming it was redesigned today. Some inherited sample references remain schematic; implementation must preserve the actual current component fields and actions.

| Route / page | Decision and reference |
| --- | --- |
| `/dashboard` as platform admin | Retain current Administration pulse and white activity/attention cards. Current source takes precedence over older dashboard mockups. |
| `/dashboard` as manager; `/workspace/dashboard` | Retain existing portfolio/dashboard cards; apply contained empty/error treatment to individual sections. |
| `/setup` | Retain surfaced checklist and three-step setup; references 128:4137 and 128:3820–128:4040. |
| `/properties` | Retain directory/detail split and in-panel add/edit; revised reference 172:2481. Existing form 134:4535 and unit form 134:4675 remain. |
| `/tenants` | Existing directory/profile structure 171:12701; retain existing empty-state placement. Retain stepped add-tenant drawer and plain edit drawer. |
| `/leases` | White filters/results surface 171:12850; retain two-step drawer. |
| `/leases/:id` | Retain terms/history surfaces, reference 52:2209. Existing lifecycle confirmation remains a dialog. |
| `/billing` | White summary/filters/results surface 171:12975. Retain generation confirmation; widen and reflow charge drawer. |
| `/billing/invoices/:id` | Retain line items, totals, payments and note surfaces, reference 52:3305. Record payment becomes the proposed modal. |
| `/billing/receipts` | White filter/results surface 171:13117. Keep errors/loading inside it too. |
| `/billing/receipts/:id` | Retain printable receipt, reference 136:4668. Preserve RCT prefix and reason-required reversal dialog. |
| `/maintenance` | New empty, board, filter and mobile proposals linked above. |
| `/maintenance/:id` | Retain update/assignment surfaces, reference 52:3779. Retain existing schedule/assignment dialog and access/photo fields. |
| `/reports` | White work surfaces 171:13221 (rent roll) and 171:13348 (arrears). Include occupied/total units in rent-roll metrics. |
| `/beta-signups` | White empty workspace 172:2205; same container surrounds populated table and applicant detail. Keep role/status/early-access/search filters and existing add drawer/email controls. |
| `/profile` | Retain existing white account and identity sections, reference 29:1443. |
| `/security` | Retain white account-protection section and existing setup/confirmation behavior, reference 29:1218. |
| `/admin/settings` | White card retained; new scope reference 172:2360 shows only actual assistant availability/configuration state. |
| `/admin/workspaces` | White summary/filter/results workspace 171:13461. Retain two-step creation drawer. |
| `/admin/workspaces/:id` | Retain members/properties/activity cards, reference 53:3671. Ownership transfer and support reason become modals; workspace profile stays a drawer. |
| `/admin/users` | White filters/results surface 171:13623; keep conditional account fields in create-user drawer. |
| `/admin/users/:id` | Retain membership/profile/security cards, reference 85:1686. Profile edit and membership change become modals. |
| `/admin/identity-checks` | New queue and decision proposals linked above. Preserve download-only document access, masked number, conditional rejection reason and audit semantics. |
| `/admin/audit-log` | White filter/results surface 171:13779. Keep audit detail in a drawer for long metadata. |
| `/admin/outreach` | White filters/contact results surface 171:13928. Retain stepped contact drawer. |
| `/admin/outreach/contacts/:id` | Retain existing overview/history/sequence cards, reference 112:3515. |
| `/admin/outreach/sequences` | Retain split sequence/template editor sections, reference 112:3801. Short New sequence becomes a modal; long template editing stays in its drawer/editor. |
| `/admin/outreach/review` | Retain queue and message-preview white sections, reference 112:4100; preserve disabled sending and existing safeguards. |
| `/admin/outreach/outbox` | White filter/results surface 171:14094. Keep long message preview in a drawer. |
| `/admin/outreach/settings` | Retain grouped white settings surface, reference 131:4959. |
| `/login` and reset/2FA states | Retain established auth panel and click-through introduction. That introduction is separate from a first-run in-app tour. |
| `/register` | Retain current availability gate and grouped names. No registration-policy changes. |
| Unimplemented tenant-portal and tour concepts | Remain future concepts; existing Tenant page mockups do not authorize implementing new endpoints or workflows. |

## Overlay decisions

Modals suit payment recording and short admin actions because each is one focused submission. Use desktop widths around 560px, 640px for payment. Keep the current screen mounted behind the overlay. Narrow screens stack related fields; short dialogs fit available viewport space and long content scrolls vertically with reachable actions.

Keep drawers for tenant creation/editing, lease creation, maintenance requests, new charges, vendors, beta signup, create user/workspace, workspace profile editing, Outreach contacts/templates/import, workspace search and audit/message detail. Keep steps inside long creation drawers. Property and unit editing retain their existing panel. Setup retains its route. Existing destructive, payment-reversal and security confirmations remain dialogs.

Implementation after approval must preserve focus trapping/restoration, Escape behavior, pending-submission protection, validation, conditional controls, current permissions and unchanged API calls. Shrinking must apply to grid children and Fluent input/dropdown/select/textarea roots. Breakpoints must follow the actual overlay space, rather than only the browser width. Tables may have contained horizontal scrolling when necessary; forms should reflow without it.

White means the light-theme paper token. Dark mode continues to use its corresponding surface token. Preserve full-width layouts with page gutters and avoid nested decorative cards.

## Validation and next phase

All proposal trees are native editable Figma frames, text, vectors and existing component instances, using the established variables and Figtree/Montserrat styles. Image-filled nodes are the existing small brand mark, not flattened page screenshots. Structural checks cover fonts, descendants and horizontal bounds; inherited filter/table overflow was corrected. Representative desktop, mobile, validation, dark and admin compositions were inspected and corrected in Figma. This does not substitute for browser testing after implementation.

The design-only stage was followed by the approved implementation and validation below. Next is guided access for first-time users: a skippable, role-aware tour with a way to replay it, grounded in the approved navigation and actual available features. The tour itself is not implemented in this pass.

## Approved implementation and verification

Implemented on 24 October 2026 following approval of the corrected designs:

- Maintenance retains its existing JSX structure, toolbar, board/list switch, lane vocabulary, request cards and per-lane empty states. Styles now give lanes white paper surfaces, readable empty text and consistent desktop height, with shorter stacked lanes on mobile. Request cards use a soft contrasting surface.
- Shared record toolbars and admin filters gain paper backgrounds and padding in place. Identity's naked summary becomes a paper surface without moving it or merging it with filters/results. Existing white empty states and detail/settings cards are retained. Loading surfaces remain white; nested loading/filter areas avoid additional padding inside existing cards.
- Added a shared Fluent `FormModal`, using the existing validation/focus helpers and theme tokens. Record payment uses its 640px variant; fields reflow according to the available modal width. Its body scrolls vertically on short screens while actions remain reachable.
- Identity decision, user profile editing, workspace membership, support-access reason, ownership transfer and New sequence use focused modals. Long forms and contextual readers retain their drawers. The charge drawer gets 720px width and container-based line reflow. Fluent controls can shrink inside both overlay types.
- Modal header alignment keeps Close beside the title. Shared server-error focusing now waits for mutation-disabled controls to re-enable before attempting focus; this was verified with an actual frontend mutation against a mocked error response.

Existing hooks, API paths, payloads, permissions and backend validators are unchanged. The first-time tour remains the next phase.

Verification:

- Final `npm run build` passes. The existing large-bundle advisory remains.
- All six existing focused Node tests pass (`formFlow.test.mjs`, `supportContext.test.mjs`).
- Browser checks use the real local React application with fictional API responses intercepted by Playwright. No backend data, emails, actual payments or support access are created. Payment success verifies receipt navigation and rendering; it does not verify a live backend transaction.
- Maintenance empty/populated board, preserved four lanes, board/list switch and responsive widths pass. Identity keeps its separate sections; rejection validation, Escape and opener focus restoration pass.
- Payment amount validation, payment-method selection, server field error/focus, pending dismissal protection, disabled submission and receipt success/navigation pass. At 390px, 720px, 1440px and 2149px, no form/page horizontal overflow was observed and actions were inside the viewport, including a 500px-high screen.
- Profile/membership/support/ownership/sequence modal checks, charge-drawer reflow, dark surfaces and reduced-motion checks pass. Shared toolbar/filter pages (tenants, leases, receipts, users, workspaces, audit log, Outreach and beta signups) pass desktop/mobile document-overflow checks. No runtime page errors were recorded in the passing run.
- Final screenshots were visually inspected for payment light/dark, Maintenance empty and Identity empty, against the approved structure and styling. Native Fluent controls and existing app chrome are retained rather than replacing them with schematic Figma controls.
- `git diff --check` passes. Source changes are limited to frontend presentation and shared overlay focus behavior; this document records the implementation.

Ignored local evidence: `output/playwright/surface-review-check.cjs`, `surface-review-results.txt`, and `surface-*.png`. The earlier interrupted runs included harness corrections for sidebar resize timing, starting theme and missing receipt fixture fields; the passing result supersedes those runs.
