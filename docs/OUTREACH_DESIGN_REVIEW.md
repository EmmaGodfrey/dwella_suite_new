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

## Next step

Review these frames before frontend code, as required by the outreach plan's
"Admin screens (Figma first)" section: **"Stop for the user's review before frontend
code."** Apply feedback here first. Backend Phase 1 can proceed independently with
staff-only contacts/templates/sequences, render validation, suppression, CSV preview
and audited writes, with permission and failure-path tests.

Before enabling the sending engine, confirm the monitored sender mailbox/provider,
the influencer offer and the initial daily cap. The design illustrates a starting cap
of 10; production configuration remains disabled until explicitly configured.
