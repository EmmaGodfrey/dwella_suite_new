# Outreach management

Implemented on 23 October 2026 after the user approved Claude's refined Figma
designs. The current slice covers the admin API and frontend management/review
flows (plan Phases 1 and 3). **The scheduled outreach sending engine and IMAP reply
detection are not implemented yet.** No outreach message is sent by approving it,
resuming a sequence or changing the pause preference.

## Setup and use

Apply migrations and seed the editable starter content from `backend/`:

```powershell
.venv/Scripts/python.exe manage.py migrate
.venv/Scripts/python.exe manage.py seed_outreach_templates
```

The seed command creates influencer partnership, agent beta invitation and early
tester check-in sequences. It adds no contacts, sends no email, and leaves existing
named sequences/templates intact. Configure the signature and sender first name
in Platform → Outreach → Settings before previewing the starter messages. Leave
the influencer offer blank until it has been decided; that sequence cannot be
approved while the offer is missing.

The Platform sidebar opens Contacts, with tabs for Sequences, Review queue, Outbox
and Settings. Contacts require a name and provenance; email is optional for a
WhatsApp-only contact but required for enrollment and account access. Search,
filters and pagination run on the server. Contact detail includes notes, account
access, activity, expandable rendered message history and enrollment controls.

CSV import accepts up to 500 rows and 1 MB. Map columns and inspect valid,
duplicate, suppressed and invalid rows before confirmation. The signed preview
expires after ten minutes and can be committed once. Confirmation revalidates
rows against current contacts and suppression; it never overwrites duplicates.
Imports, private exports and scratch contact data must not be committed to Git.

Templates have editable subject, email body and WhatsApp body, merge-field chips,
an active flag and version numbers. Use a selected contact to preview the saved
template. Sequence delays are relative to the previous step; the initial delay
is measured from enrollment. Approved sequence structure is protected; create a
new sequence to change it. Template edits leave approved message copies intact.

## Review and access safeguards

All API resources require platform staff/superuser access. They are platform
resources and do not require a landlord support session. Writes use the standard
API envelope, validation, the existing platform write throttle and atomic audit
recording. Contact content and email bodies are not copied into audit metadata.
Django admin is read-only for outreach data, including suppression.

Enrollment first enters `pending_review`. The review queue renders every step and
shows missing fields in plain language. Save a changed opening line to refresh
the preview before approval. A signed ten-minute preview binds approval to the
rendered content and recipient. Missing, tampered, expired or stale previews are
refused. Approval stores rendered copies of all steps; repeated approval cannot
create another copy. Bulk approval applies to ready entries on the current page
and is atomic if any selected entry becomes invalid.

Only one live enrollment per contact is allowed. Pause, resume, stop and schedule
next-step actions update enrollment state; eventual sending must still enforce
the window, cap, pause and suppression rules. Stop an approved sequence before
editing its contact details, then enroll and review the updated message again.

Marking replied/interested/partner/not interested stops live follow-ups. Do not
contact creates permanent email suppression. Suppression survives contact deletion,
recreation and attempted status changes. Suppressed contacts cannot enroll, open
a WhatsApp message or receive early access. WhatsApp produces a draft for manual
sending; it does not send messages itself.

Early access explicitly sends the existing transactional beta account email; it
requires beta delivery to be configured and `APP_BETA_EMAILS_ENABLED=true`. It
finds/links the beta signup, provisions the ordinary landlord account, delivers
the access email once, and stops welcome/countdown mail. The existing Add signup
drawer has a Give early access now toggle, plus a derived Early access badge and
filter. SMTP failures return an actionable error; audit failure prevents delivery.
No test in this work used a real SMTP connection.

Tester check-ins are queued for review after early access, rather than silently
approved: the review queue remains the only place that approves outreach sending.
Their initial Day 3 delay is retained on approval. Reply/suppression history is
never cleared to force a new automated sequence.

## API map

All routes below start with `/api/v1/platform/outreach/`:

| Resource | Actions |
| --- | --- |
| `contacts/` | List, create, retrieve, patch, delete |
| `contacts/{id}/status/` | Mark replied/interested/partner/not interested/do not contact |
| `contacts/{id}/activity/` | Paginated audit activity |
| `contacts/{id}/early-access/` | Deliver transactional account access once |
| `contacts/import-preview/`, `contacts/import-confirm/` | Preview/mapped import, then signed confirmation |
| `templates/` | List, create, retrieve, patch; archive using `active=false` |
| `templates/{id}/preview/`, `templates/{id}/whatsapp/` | Render for a contact; prepare manual WhatsApp draft |
| `sequences/` | List, create, retrieve, patch with ordered `steps` |
| `enrollments/` | List, create, retrieve, patch pending opening line |
| `enrollments/{id}/preview/` | Render and issue signed `preview_token` |
| `enrollments/{id}/approve/` | Approve with `preview_token` |
| `enrollments/approve-many/` | Approve `ids` with per-id `tokens` |
| `enrollments/{id}/state/` | `pause`, `resume`, `stop`, `send_next` |
| `messages/` | Read-only rendered message history |
| `settings/`, `summary/` | Admin preferences and live totals |

## Validation and remaining work

Validation for this slice: full SQLite suite **449 passed / 2 PostgreSQL-only
skips**; full isolated PostgreSQL 17 suite **451 passed**, including real row-lock
tests. Django check, migration consistency, Ruff and the frontend production build
passed. Browser checks covered contact validation/create, missing-field review,
settings persistence, opening-line edits, approval/outbox, template editing/preview,
CSV preview/confirmation, suppression and the disabled early-access toggle when
beta email is off. Light/dark, 390px mobile and viewport reflow equivalents of
67%/200% zoom were inspected. Scratch data and artifacts remain ignored.

Before Phase 2, confirm the sender mailbox/provider, influencer offer and initial
daily cap as required by the [plan](OUTREACH_PLAN.md). Then implement the separate
mail connection, send window/cap/jitter, idempotent scheduled delivery, unsubscribe,
bounce handling, test send and scheduler integration. Phase 4 adds IMAP detection
and platform reply notifications; automatic opener drafting remains optional.
Confirm opt-out wording with qualified advice before scaling outreach, per the plan.

Sending, deployment, staging tags and pushes have not been authorized or performed
as part of this implementation.
