# Outreach design review

Prepared 23 October 2026 from Claude's [outreach plan](OUTREACH_PLAN.md), after
finishing the admin console. Designs are editable native layers in the Dwella
Figma file, on **Admin (Platform)**, to the right of the existing admin screens.

## Review map

| Surface | Figma |
| --- | --- |
| Contacts, filters and sending summary | [Contacts](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=112-3188) |
| Profile, activity, sequence and manual actions | [Contact detail](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=112-3515) |
| Sequence steps and merge-field editor | [Sequences and templates](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=112-3801) |
| Rendered first email and approval | [Review queue](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=112-4100) |
| Delivery, cap and stopped messages | [Outbox](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=112-4388) |
| Sender, signature, sending window and pause | [Settings](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=112-4673) |
| Business contact and provenance | [Add contact drawer](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=114-3545) |
| Column mapping, duplicates and invalid rows | [CSV preview](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=114-3730) |
| Immediate account access and tester check-ins | [Early-access confirmation](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=114-3872) |
| Required partnership offer blocks approval | [Missing offer](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=114-3993) |
| Desktop dark theme | [Dark review queue](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=114-4257) |
| Mobile light theme | [Mobile review queue](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=114-4329) |
| Mobile dark theme | [Mobile dark](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=114-4362) |
| Empty, loading, error, paused, suppressed and failed delivery | [States](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=115-3935) |
| Give early access while adding a beta signup | [Beta signup](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/Dwella?node-id=115-4236) |

## Product decisions represented

The admin manages a small selected contact list, chooses an editable sequence, and
reviews the rendered first email before approving it. Missing required merge fields
block approval. Follow-ups stop on reply, opt-out or bounce. Suppression is permanent
and applies to both enrollment and early-access actions. CSV import previews mapping,
duplicates and invalid rows before saving anything.

Early access sends account setup immediately, links the beta signup, stops countdown
mail and queues Day 3/10 check-ins. The beta-signup option uses the same behavior.
WhatsApp remains a manual action from contact detail. The sender mailbox and
partnership offer remain user decisions; no real mailbox or offer is invented.

All contacts, counts and activity shown are fictional examples. This review set does
not import private contacts, configure SMTP, approve outreach or send messages.
Outreach frontend and engine code have not been implemented.

## Design and validation

The screens reuse the local Dwella sidebar, buttons, text fields, badges, icons,
typography styles and theme variables. Content uses auto layout, desktop gutters and
stacked mobile messages. Figtree and Montserrat are the only rendered font families.
Representative desktop, drawer, message and dark/mobile compositions were visually
checked. The final native-node check found no horizontal text overflow across all
15 frames. Implementation must keep the screens accessible and reflowing at zoom.

## Claude review (23 October 2026)

Reviewed all 15 frames against the outreach plan. Fixed in Figma, preserving frame IDs:

- Page-header actions now sit on the right content edge (the title column was a
  fixed 768px, leaving buttons floating about 120px short).
- Sidebar account email truncates on one line instead of wrapping ".co" onto a
  third line.
- Contacts and Outbox status columns use `Badge` tones (New/Scheduled info,
  Queued/Blocked warning, Interested/Replied success, Do not contact/Opted out
  danger). Actionable "Next step" cells use `text/link`; "Suppressed permanently"
  stays plain because it is not an action.
- Segment, Status and CSV column-mapping fields show the dropdown chevron, so they
  read as selects. Apply filters is bottom-aligned with the inputs.
- Review queue (light and dark): the open item has a selected surface, and each
  item's state is a badge. The footnote no longer says "Sending is currently
  paused", which contradicted the Outbox (2 sent, one scheduled at 14:20).
- Missing offer: the error under the offer field said "Enter a valid email
  address." It now says "Add the partnership offer before approving.", and a
  disabled Approve email button shows what is blocked.
- Sequences: merge fields are insertable chips, and the list now matches the
  template ({salutation} was used but not listed).
- Beta signup: "Give early access now" is a real `Toggle`, not a badge.
- Settings frame renamed "Settings — Before mailbox setup" to explain why it
  shows "Not configured" and "Sending paused" alongside running Outbox examples.

Still open for implementation (not blocking design approval):

- Contact detail lacks the plan's Stop and Send next step now actions, and the
  activity timeline should expand to show each sent email's rendered text.
- Settings signature and the template message body should be editable text
  areas in code, not static text.
- Mobile review queue needs the app's mobile top bar/navigation and the personal
  opening line field; its email copy is a shortened variant of the desktop one.
- Loading state should use skeleton rows, not a "Loading…" button.
- Plan placed early access in the existing Add signup drawer; the frame shows a
  full page. Implement it as the toggle inside the existing drawer.

## Next step

The user approved Claude's refined frames on **23 October 2026**, lifting the
outreach frontend gate. The management API and frontend are implemented; see
[OUTREACH.md](OUTREACH.md) for usage, safeguards, validation and the remaining engine
work. Claude's implementation notes above were applied, including editable message
and signature text areas, merge-field chips, message expansion, enrollment actions,
mobile shell/opening line, skeleton loading and the existing signup drawer toggle.

Before enabling the sending engine, confirm the monitored sender mailbox/provider,
the influencer offer and the initial daily cap. The design illustrates a starting cap
of 10; production configuration remains disabled until explicitly configured.
