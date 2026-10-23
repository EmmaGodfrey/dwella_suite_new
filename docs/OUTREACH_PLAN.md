# Partner and influencer outreach — plan

Written 22 October 2026 for Codex to carry out. Owner: the platform admin (the user).

## What the user asked for

> Let's talk about the list we send emails. Are we able to automate this? I can't be
> writing messages by hand, so add an emailing part to email some individuals… emails
> for sending to people as EG Labs for Dwella, especially these influencers, as a
> partnership.

So: a small outreach tool in the admin console. The admin keeps a list of people
(influencers, estate agents, property managers, partners), picks a ready-made message
sequence, checks it once, and Dwella sends the first email and the follow-ups on a
schedule, from EG Labs, until the person replies or opts out. No message is typed by
hand.

This is **personal one-to-one outreach to a short, hand-picked list**. It is not a
newsletter or bulk mailer. Every design choice below protects deliverability and the
EG Labs name: low daily caps, plain personal-looking emails, an opt-out in every email,
and sending stops the moment someone replies.

## How it fits what exists

- The Django mail stack and SMTP settings were set up for the beta emails
  (`apps/marketing/emails.py`, `EMAIL_*` in `.env.prod`). The `beta-mailer` compose
  service already runs a management command every 15 minutes.
- `BetaApplication` already stores applicants, with an unsubscribe flow, a send log
  (`BetaEmail`) and the "record before send, remove on failure" idempotency pattern.
  Reuse these patterns; don't reinvent them.
- The admin console plan (`docs/ADMIN_CONSOLE_PLAN.md`) defines the Platform sidebar
  group, staff-only permissions (`IsPlatformAdmin`) and `apps/audit/services.record_event`.
  Outreach goes under that group as **Outreach**.
- Contacts the user already found (TikTok agents and influencers, Zed Realtor) live in
  the user's private notes, **not** in the repo. The user adds them through the new
  screen or a CSV import after the build. Never commit contact data, seed files with
  real people, or exports.

## Sender identity

- Emails come from a person, not a robot. Use a configured sender, e.g.
  `Emmanuel Godfrey, EG Labs <hello@…>`. **The user decides the address.** Recommended:
  a mailbox on the EG Labs domain that the user reads, with replies going to it.
- Use a separate SMTP connection from transactional mail, so a spam complaint about
  outreach can't hurt password-reset and beta emails. New settings:
  `OUTREACH_EMAIL_HOST`, `_PORT`, `_HOST_USER`, `_HOST_PASSWORD`, `_USE_TLS`,
  `_USE_SSL`, `OUTREACH_FROM_ADDRESS`, `OUTREACH_FROM_NAME`, `OUTREACH_REPLY_TO`,
  `OUTREACH_ENABLED` (default **false**), `OUTREACH_DAILY_CAP` (default 25).
  If unset, fall back to the main `EMAIL_*` connection only when the user explicitly
  sets `OUTREACH_USE_DEFAULT_CONNECTION=true`.
- The signature (name, title, phone, links to dwella.properties and @my.dwella) is
  edited in the Outreach settings screen and stored in the database. Never hard-code
  it, and keep the user's phone number out of the repo.
- Launch checklist for the user, documented by Codex: SPF, DKIM and DMARC on the
  sending domain; a test send to Gmail and Outlook that lands in the inbox; start at
  about 10 a day for the first week.

## Data model (new app `apps/outreach`)

| Model | Purpose / key fields |
| --- | --- |
| `Contact` | name, first_name (for greetings), salutation override (e.g. "Mr Samiselo"), email, phone, whatsapp, organization, role/title, segment (`influencer`, `agent`, `property_manager`, `landlord`, `partner`, `other`), platform (`tiktok`, `instagram`, `facebook`, `linkedin`, `website`, `referral`, `other`), handle, profile_url, audience_size, town, notes, tags, status (`new`, `queued`, `contacted`, `replied`, `interested`, `partner`, `not_interested`, `do_not_contact`, `bounced`), source, owner (admin user), last_contacted_at, replied_at. Email is unique (case-insensitive) when present |
| `Template` | name, segment, subject, body (plain text with merge fields), is_follow_up, active. Versioned by editing; messages store the rendered copy |
| `Sequence` | name, description, steps (`SequenceStep`: order, template, wait_days after the previous step, `only_if_no_reply` always true) |
| `Enrollment` | contact + sequence, status (`scheduled`, `active`, `paused`, `completed`, `stopped_reply`, `stopped_optout`, `stopped_bounce`, `cancelled`), next_step, next_send_at, personal_line (optional custom opener), approved_by/approved_at |
| `OutreachMessage` | enrollment, step, rendered subject and body, `message_id` header, status (`pending`, `sent`, `failed`, `bounced`), sent_at, error. The idempotency record, like `BetaEmail` |
| `Suppression` | email (unique), reason (`unsubscribed`, `bounced`, `manual`, `complaint`), created_at. Checked before **every** send, in every sequence, forever |
| `OutreachSettings` | singleton: signature, send window, daily cap override, paused flag |

All admin writes call `record_event` (`outreach.contact.created`,
`outreach.enrollment.approved`, `outreach.message.sent`, …).

## Sending rules (the engine)

A management command, `send_outreach_emails`, is added to the existing `beta-mailer`
loop. It:

1. Does nothing unless `OUTREACH_ENABLED` is true and the settings aren't paused.
2. Sends only on **Monday–Friday, 08:00–17:00 Africa/Lusaka**, and only within the
   daily cap (count `sent` messages today).
3. Sends at most 3 per run, with a random 20–90 second gap between sends, so mail
   doesn't go out in bursts.
4. Never sends to a suppressed or `do_not_contact` address, or to an enrollment whose
   contact has replied. Never sends the same step twice: record `pending` first and
   delete it on SMTP failure, like the beta emails.
5. **Renders merge fields** and refuses to send if any `{field}` is left unfilled. The
   enrollment shows "Missing first name" instead, so no "Hi {first_name}" ever goes out.
6. Sends a **plain-looking** email: a text part, plus minimal HTML that is just
   paragraphs and the signature. No images, no tracking pixel, no click-tracking
   redirects. Personal emails without tracking land in the inbox more often. Sets
   `List-Unsubscribe` (one-click) and a visible one-line opt-out:
   "Not for you? Reply 'no thanks' or [stop these emails]."
7. Threads follow-ups as replies to the first email (`In-Reply-To` / `References`
   with "Re: <first subject>"), the way a person would follow up.
8. Marks hard bounces from SMTP errors as `bounced`, and suppresses the address.

**Reply detection (Phase 4).** The command polls the reply mailbox over IMAP
(`OUTREACH_IMAP_HOST/USER/PASSWORD`, read-only, recent messages only). It matches the
sender address or `In-Reply-To` to a contact, then sets `replied`, stops the
enrollment and raises a bell notification ("Chrispin Samiselo replied"). It never
stores email bodies beyond a 300-character snippet. Until Phase 4 ships, the admin
clicks **Mark replied** on the contact. A reply that says "stop"/"unsubscribe" →
suppress.

## Admin screens (Figma first)

Under **Platform → Outreach**, with tabs:

1. **Contacts**: table (name/org, segment, platform + audience, status, last
   contacted, next email), search and filters, an add-contact drawer, and **Import
   CSV** (column mapping, preview, duplicate and invalid-email report, nothing saved
   until confirmed). Row actions: Enroll in sequence, Mark replied / interested /
   partner / not interested, Do not contact, Copy WhatsApp message.
2. **Contact detail**: profile, timeline (every email sent, with its rendered text,
   replies and status changes), notes, and the current enrollment with Pause / Stop /
   Send next step now.
3. **Sequences and templates**: a list and an editor with merge-field chips
   (`{first_name}`, `{salutation}`, `{organization}`, `{platform}`, `{handle}`,
   `{audience_size}`, `{town}`, `{personal_line}`, `{sender_first_name}`), a live
   preview against a chosen contact, and a step timeline (Day 0, Day 4, Day 10).
4. **Review queue**: the only place sending is approved. For newly enrolled contacts
   it shows each first email fully rendered. Actions: approve one, **approve all**,
   edit the personal line, remove. Follow-ups need no second approval but can be
   stopped at any time.
5. **Outbox / activity**: today's sent / remaining cap / scheduled, failures and
   bounces, plus a pause-all switch.
6. **Settings**: sender name and signature, send window, daily cap, a **Send test to
   me** button.

**WhatsApp.** Many leads only have WhatsApp. "Copy WhatsApp message" renders the same
template's short version and opens `https://wa.me/<number>?text=…`. The admin still
taps send in WhatsApp; nothing sends automatically there, and the contact's timeline
records it as "WhatsApp opened".

Follow the existing design standards: Dwella Figma file `aHlQPzHBsvGR4rNoabRQyW`, page
"Admin (Platform)", using the updated sidebar, top bar and card patterns from
`docs/ADMIN_CONSOLE_DESIGN_REVIEW.md` ("Design pass"). Also follow
`.agents/skills/dwella-impeccable-ui` and `dwella-taste-ui`. Use edge-to-edge
content, rem type, and check light and dark. **Stop for the user's review before
frontend code.**

## Starter sequences (seed as editable templates, not code constants)

The tone is warm, short and specific, from Emmanuel at EG Labs. The influencer offer
has placeholders until the user confirms it (see Decisions).

**Influencer partnership** (segment `influencer`):

- *Day 0*: subject "Dwella × {handle}: partnership idea"
  > Hi {first_name},
  >
  > {personal_line}
  >
  > I'm Emmanuel from EG Labs in Lusaka. We're building Dwella, a property management
  > app for Zambian landlords and agents: rent tracking, receipts, reminders and
  > maintenance in one place. Our beta opens on 18 November.
  >
  > Your audience is exactly who we're building for, so I'd love to explore a
  > partnership. We can offer {offer}. Would you be open to a 15-minute call this
  > week or next?
  >
  > {signature}
- *Day 4*: "Re: …"
  > Hi {first_name}, just bringing this back to the top of your inbox. Happy to send a
  > short demo video first if that's easier. {signature_short}
- *Day 10*: "Re: …"
  > Hi {first_name}, I'll leave it here so I don't crowd your inbox. If a partnership
  > around the 18 December launch is interesting later, just reply and we'll pick it up.
  > {signature_short}

**Agent / property manager beta invite** (segments `agent`, `property_manager`,
`landlord`):

- *Day 0*: subject "Free beta access to Dwella for {organization}"
  > Dear {salutation},
  >
  > {personal_line}
  >
  > I'm Emmanuel from EG Labs. We're building Dwella, a property management tool made
  > for how rentals work in Zambia: tenants, leases, rent and receipts, arrears and
  > repairs in one place, on your phone or computer.
  >
  > We're opening a free beta on 18 November for a small group of agents and property
  > managers, and your feedback would shape what we build. You can reserve a place at
  > dwella.properties, or reply and I'll set up your account for you.
  >
  > {signature}
- *Day 5*: a short nudge. *Day 12*: a polite close-out.

`{personal_line}` is optional. An empty line is removed cleanly. It's where a sentence
like "Loved your video on finding rentals in Ibex Hill" goes.

**Optional, Phase 5: drafted personal lines.** A "Suggest opener" button on the review
queue drafts `{personal_line}` from the contact's notes, platform and handle using the
Anthropic API. Use the current recommended Claude model, per the `claude-api` skill at
build time; the key goes in `ANTHROPIC_API_KEY` in `.env`. The admin always sees and
approves it before sending. Nothing is sent from an AI draft without approval, and
contact data sent to the API is limited to name, organization, platform, handle and
the admin's notes.

## Early access (testers before 18 November)

The user wants chosen people to use Dwella **now**, before the beta opens.

**Already works today, on `develop` at `99b3a59`:** Beta signups → Add signup (turn the
welcome off) → **Send sign-in details now**. This creates a landlord account and emails a
one-time set-password link right away. Before beta day the email reads "You're in early:
your Dwella account is ready" and asks for feedback. Once sign-in details are sent, no
welcome or countdown email follows. It needs `APP_BETA_EMAILS_ENABLED=true` and working
SMTP. To build:

1. **Beta signups.** Add a "Give early access now" option in the Add signup drawer, which
   creates the signup without a welcome and sends sign-in details in one step. Add an
   "Early access" badge and filter, derived from an access email sent before
   `BETA_OPEN_DATE`; no new status is needed.
2. **Outreach.** Add a **Give early access** action on a contact, and an "Early access"
   option in the review queue. It finds or creates the matching `BetaApplication`
   (source `admin`, linked to the contact), sends sign-in details immediately and
   sets the contact to `partner`/`interested`. It requires an email address and isn't
   available to suppressed contacts.
3. **Early tester check-ins.** Seed an "Early tester check-ins" sequence: Day 3 "How's it
   going so far?" and Day 10 "Three quick questions" (what they tried, what got in
   the way, would they recommend it). It stops on reply like every sequence and starts
   automatically after early access.
4. Tests: early access creates exactly one account and one access email; the contact
   is linked; no countdown email afterwards; suppressed or email-less contacts are
   refused; non-staff get 403.

## Phases

Small, focused commits within each phase (see the shared memory feedback). Work on
`develop`; no push to main and no deployment without the user's instruction.

0. **Figma:** the screens above, then the user's review.
1. **Models, migrations, admin-only API:** CRUD for contacts, templates and
   sequences; CSV import (validate, dedupe, preview then commit); merge-field
   rendering and validation; suppression; audit events. Tests cover: non-staff 403,
   validation, duplicate emails, a CSV with bad rows, render failures on missing
   fields, suppression always wins.
2. **Engine:** `send_outreach_emails`, the separate SMTP connection, send window and
   cap, jitter, threading headers, unsubscribe endpoint (signed token, generic
   response), bounce handling, test send, and adding it to the `beta-mailer` loop.
   Tests use a frozen clock and `locmem` mail: window and cap edges, idempotency
   under a double run, stop on reply/opt-out/bounce, `OUTREACH_ENABLED=false` sends
   nothing.
3. **Frontend screens** after Figma approval: hooks in `src/Services/`, the Platform
   nav item, review queue, WhatsApp copy.
4. **Reply detection over IMAP** plus bell notifications.
5. **Optional drafted openers**, only if the user wants them.

## Rules and compliance

- Send only to people with a public business contact (their bio, site or listing) or
  who gave their details. No scraped or bought lists, and no automated contact
  discovery.
- Every email identifies EG Labs and Dwella, has an honest subject and a working
  opt-out, and stops at the first reply. Suppression is permanent.
- Keep a record of where each contact came from (`source`, `profile_url`). Zambia's
  Data Protection Act (2021) and the Electronic Communications and Transactions Act
  (2021) apply to direct marketing. Codex should note in the docs that the user
  should confirm the opt-out wording with someone qualified before scaling up.
- Contact data is personal data: staff-only access, audited, never in Git, exports
  or logs.

## Decisions for the user (before Phase 2)

1. **Sender address** (e.g. `emmanuel@<eglabs domain>`) and which mail provider
   sends it.
2. **The influencer offer** to fill `{offer}`. For example: free Dwella for their own
   rentals, a referral commission per paying landlord, a paid launch-post fee, or
   co-created content around the 18 December launch.
3. **Daily cap** to start with. Recommended: 10 a day in week one, then 25.
