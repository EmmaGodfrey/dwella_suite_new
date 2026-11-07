# Guided tour refresh — design review

Status: proposed on 2026-10-28; frontend implementation awaits design review.
No application code, migration, deployment or live user preference changed.

User request: remove the always-present tour interruption, spotlight real UI
with a dimmed/blurred overlay, guide property managers and tenants through their
modules/basic flows/settings, and persist a don't-show-again choice.

## Review frames

All frames extend the approved Account access & setup page in the existing
Dwella Figma file, without replacing the approved originals.

| View | Figma |
| --- | --- |
| Start here / behavior and coverage | [264:469](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=264-469) |
| Optional welcome | [264:477](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=264-477) |
| Manager spotlight | [264:628](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=264-628) |
| Tenant spotlight | [264:846](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=264-846) |
| Settings replay and preference | [264:1036](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=264-1036) |
| Phone spotlight and docked guide | [264:1186](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=264-1186) |
| Dark manager spotlight | [264:1296](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=264-1296) |
| Failed opt-out save and retry | [264:1393](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW?node-id=264-1393) |

Screens are editable reference designs using existing Dwella shells, coachmark,
button/toggle instances, fonts and theme variables. They illustrate behavior
and placement rather than replacing current screens with the older shell.

## Quiet availability and persistence

- Remove the permanent header launcher, including its error/retry substitute.
  Mount the tour independently so opening it does not occupy header space.
- Manual entry is Settings → Account → Product tour. Show Replay; show Resume
  when saved progress is incomplete. Loading/errors/retries stay in that section.
- Offer an optional welcome once for eligible new users, after setup/mailbox
  gates. Existing skipped/completed users do not get another unsolicited welcome.
- Not now closes the invitation and persists its dismissed state. Pausing or
  Escape saves the current position and closes the overlay without reopening it
  on the next page. Completed tours stay closed.
- Don't show again persists an account preference on the server, across devices
  and future tour revisions. Workspace-specific progress stays separate. A manual
  replay does not silently re-enable automatic prompts.
- New steps never restore the header launcher or bypass an opt-out. New guidance
  can be offered inside Settings without interrupting normal work.
- Failed preference saves are explicit, retain the draft and allow retry. Do not
  tell the user a cross-device preference was saved before server confirmation.

## Spotlight and navigation

Keep the highlighted UI clear. Dim and blur the area outside it. Position a
single coachmark beside the target on desktop and below the visible target on
phones. Bring targets into view without covering them. Use a short fade for
continuity and respect reduced motion.

Trap focus in tour controls; Escape pauses. The background, including the
highlighted target, cannot trigger an accidental submit or payment. Guidance
does not create sample records, submit forms, send messages, start signing,
change settings or move money. After the tour the user performs the real flow.

Navigate to the required route and Settings tab before finding the target. Wait
for content/layout to settle, observe relevant DOM/size changes, and recalculate
on scroll/resize. The current implementation checks for an existing selector
before navigating, which can leave generic targets on the wrong screen.

Use useful empty-state guidance when a workspace has no properties/tenants/etc.
Do not choose an arbitrary customer's record or require creating one. Disabled
features and unavailable roles must be filtered by current access. A missing or
hidden target gets a bounded fallback with Next/Pause, not endless waiting.
Do not navigate away from a dirty form without the app's existing leave guard.

## Proposed coverage

The manager sequence has 23 concise steps; the tenant sequence has 13. Keep
stable IDs from existing tours so completed work survives the expanded guidance.
The labels below describe guidance, not new write capabilities.

| Manager step | Basic flow explained |
| --- | --- |
| 1. Dashboard | Rent, occupancy and attention links |
| 2. Properties | Find a building and its details |
| 3. Units | Add property/unit and set asking rent |
| 4. Unit imports | Template → preview/errors → confirmation |
| 5. Tenants | Contact records and active/past/archived views |
| 6. Tenant imports | Template, duplicate checks and preview |
| 7. Portal invitations | Invite the correct tenant; manage access |
| 8. Leases | Connect tenant/unit; prepare a draft |
| 9. Agreements | Review document/signing states and downloads |
| 10. Renewals | New draft, changed terms and fresh signatures |
| 11. Invoices | Recurring/one-off charges and balances |
| 12. Payments and receipts | Manual record versus confirmed online payment |
| 13. Payouts | Where to inspect status; no tour-initiated transfer |
| 14. Maintenance | Report, assign, update and retain completion history |
| 15. Messages | Recipients/content preview, confirmation and history |
| 16. Reports | Locate the existing reports/exports; no reports redesign |
| 17. Notifications | Read and follow scoped alerts |
| 18. Account settings | Profile and contact details |
| 19. Workspace settings | Business, currency/timezone and issuer details |
| 20. Billing settings | Receiving details and billing context |
| 21. Notification settings | Personal channels and workspace reminders |
| 22. Security settings | Password/account protection and optional 2FA |
| 23. Tour controls | Replay/resume and saved automatic-prompt preference |

| Tenant step | Basic flow explained |
| --- | --- |
| 1. Home | Current tenancy and manager contact |
| 2. Balance | Due/overdue amounts and invoice context |
| 3. Payments | Review invoice and locate Pay; no automatic submission |
| 4. Receipts | Confirmed payment history, receipt and download/print |
| 5. My lease | Terms, current agreement and documents |
| 6. Signing | Email-verified signing handoff; no automatic activation |
| 7. Maintenance | Report a request linked to the tenancy |
| 8. Photos and access | Add evidence and explicitly choose access permission |
| 9. Repair updates | Follow progress and add a message |
| 10. Notifications | Read rent/document/repair alerts |
| 11. Contact settings | Tenant-editable details; signing email stays controlled |
| 12. Notification settings | Personal preferences and mandatory overdue notices |
| 13. Security and help | Account protection and where to replay/disable guidance |

No automatic tour for system admins, support acting mode, suspended workspaces,
unverified required accounts or tenants without an authorized portal context.
Tenant guidance must never enter manager modules, receiving accounts, workspace
administration or platform settings. Viewing a payout/settings page does not
authorize editing any payment behavior.

## Implementation and validation after review

1. Add the server-side automatic-prompt preference, role/feature-aware definitions
   and explicit dismissal behavior while retaining stable progress IDs. Use the
   existing account setup API and model patterns; no new tour dependency.
2. Move manual controls to Settings; replace the non-modal coachmark with a
   focus-managed spotlight layer. Keep all API calls in Services/hooks.
3. Cover saved dismissal across reload/revision, authorization/workspace changes,
   role/feature filtering, stable progress and malformed actions in backend tests.
   Check frontend save failure/rollback, Next/Back/Finish, tab routing, late targets,
   empty datasets, keyboard/focus restoration and reduced motion.
4. Run required backend check/Ruff/relevant tests and full suite for shared account
   behavior; build the frontend and inspect desktop/mobile/light/dark once, fix
   observed issues together and confirm. No deployment without instruction.

## Interaction changes

| Before | After | Why |
| --- | --- | --- |
| Header launcher always present | Replay/resume in Settings | Keeps everyday work quiet |
| Non-modal card and outline | Focus-managed blurred backdrop with clear spotlight | Makes the relevant control obvious |
| Immediate close/move without target readiness | Bounded target readiness and short fade | Avoids pointing at the wrong screen |
| Skip/pause only | Separate pause, dismissal and persistent opt-out | Respects the user's intended interruption level |

Review validation: eight native editable frames inspected; Figtree/Montserrat
font assertion passed; only small existing brand-logo image fills are used.
Desktop/phone/dark spotlight, Settings, welcome and save-error compositions were
visually reviewed, with clipping/overlay positioning defects corrected. This is
design validation, not application test or implementation evidence.
