# Admin console — Phase 0 design review

Prepared 22 October 2026 on `develop`. Frontend implementation is paused until the user reviews these designs. Backend Phase 1 is independent of that review gate.

All designs are on [Admin (Platform)](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=33-34). Existing Landlords, Landlord detail, Audit log and platform overview frames were updated in place. Deferred integration, messaging and settings frames were retained.

## Review coverage

| Plan item | Frames |
| --- | --- |
| Admin sidebar: Platform and acting states | [Workspaces](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=53-297), [Acting Billing](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=87-2605) |
| Workspace picker and reason dialog | [Picker](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=87-2057), [Reason](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=87-2208), [Validation](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=87-2348) |
| Acting banner, light and dark | [Light](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=87-2605), [Dark](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=87-3055) |
| Users list and filters | [Users](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=85-1096) |
| User detail and actions menu | [Detail](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=85-1686), [Menu](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=87-2486) |
| Create user: landlord/new workspace, existing member, platform admin | [Landlord](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=86-1287), [Member](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=86-1453), [Platform admin](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=86-1611) |
| Change role / add membership | [Change role and last-owner guard](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=86-1757), [Add member](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=86-1865) |
| Identity queue, approve/reject review | [Queue](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=85-2155), [Review](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=86-1973), [Reject](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=90-2829) |
| Workspace detail, members, properties, activity and actions | [Detail](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=53-3671), [Transfer ownership](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=86-2212) |
| Audit log, filters, CSV action and detail | [Audit log](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=54-665), [Event detail](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=86-2103) |
| Administration dashboard | [Dashboard](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=35-59) |
| Destructive confirmations and complete feedback states | [Confirmations](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=89-2719), [States](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=89-2947) |

Additional flows: [create workspace](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=90-2949) and [edit user](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=90-3106).

Responsive examples: [Users](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=90-3220), [acting Billing light](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=90-3295), [acting Billing dark](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=90-3363), [reason form](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella-Suite?node-id=90-3396).

## Design decisions

- White sidebar in light mode; navy primary actions and support banner; green collections/positive statuses.
- Existing Foundations components and variable bindings supply text fields, buttons, navigation items, pills, spacing, radii and themed colors. Tables retain the existing Audit log row structure.
- Figtree UI and Montserrat display styles, 32px desktop gutters, full-width desktop content. Figma text sizes map to the existing rem-based frontend tokens during implementation.
- Platform navigation stays available while acting; Overview, Portfolio and Operations are added only in that state.
- The admin retains their identity. Opening support access requires a 5–300 character reason, and the banner exposes its reason, expiry and Leave action.
- Superuser-only actions, self-protection, last-superuser and last-owner limits are explicitly represented. Permanent deletion requires an inactive user or suspended workspace and typed confirmation.
- Mobile directories become stacked records; desktop multi-column regions stack on narrow widths. Drawers become full-width on mobile. Long content uses document scrolling; filters wrap instead of imposing a centred content cap.
- Figures and people are illustrative sample data. Identity review uses a labelled secure document preview slot rather than a fabricated personal document.
- The retained landlord Billing reference includes previously proposed billing features; this phase adds support context to that existing reference. It does not authorize implementation of deferred integrations.

## Validation and handoff

Thirty editable review frames were composed. Native-node inspection confirmed text, frames, vectors and component instances; image fills are only the existing small brand mark. All rendered text uses Figtree or Montserrat. Horizontal bounds were checked across the set and corrected. Main screens, drawers, confirmations, states, mobile acting mode and light/dark acting views were visually inspected.

No frontend files were changed, so no frontend build or browser-flow claim is made for Phase 0. Figma is the review artifact. After user feedback, update these frames before starting frontend work. Backend validation and usage are documented in [ADMIN_CONSOLE.md](ADMIN_CONSOLE.md).

