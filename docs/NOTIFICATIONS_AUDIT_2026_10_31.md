# Notification coverage and proposed message credits

Date: 2026-10-31

Read-only source audit. No delivery switches, provider configuration, prices or application code changed. No live email/SMS/WhatsApp was sent. Current deployed settings and inbox delivery were not queried; deployment observations from shared memory are dated evidence only.

Later on 2026-10-31 the user authorised implementing the missing operational notifications. This audit preserves the pre-change findings; see `TRANSACTIONAL_NOTIFICATIONS_IMPLEMENTATION_2026_10_31.md` for the implementation and validation status. The WhatsApp payment-proof conversation remains a separate architecture proposal.

## Direct answer: payment received

When provider reconciliation creates a confirmed billing payment, the landlord sees **Payment received** in the application bell. Manually recorded payments use the same payment table and also appear there. The tenant gets a corresponding own-payment alert and receipt access.

There is currently no automatic rent-payment email to the landlord or tenant, and no automatic SMS/WhatsApp payment confirmation. Enabling email in Settings cannot create a missing event trigger. A receipt existing in Dwella does not mean a receipt was emailed. Starting/pending checkout is not a confirmed payment.

Gmail is simply one possible recipient inbox. Configured SMTP/email delivery can send to the saved email address; no special Gmail integration is necessary. The relevant payment/repair/lease event must first enqueue a message, which most currently do not.

Evidence: `backend/apps/notifications/views.py::live_alerts`, `tenant_alerts.py::tenant_alerts`, `billing/services.py::record_payment`, and provider reconciliation in `apps/payments/services.py`. Repository search of actual mail/queue producers found no payment-success email producer.

## What the app calls notifications

There are several separate mechanisms:

1. **Application bell:** queries existing business records and derives current alerts. `NotificationRead` stores read acknowledgements. This is not a durable event inbox with an outgoing message per alert.
2. **Scheduled rent reminders:** creates `MessageDelivery` rows for tenant email/SMS/WhatsApp, then a worker checks whether they may be sent.
3. **Manager-composed messages:** selected tenants/all reachable tenants, preview, explicit confirm, durable delivery rows. Handy can invoke the same scoped workflow. This is an intentional communication, not an automatic financial notification.
4. **Account/security email:** mailbox verification, password reset, tenant invitation and receiving-account change are direct email paths.
5. **Lease-signing email:** separate durable signing outbox for invitations, verification codes and completed copies.
6. **Beta/outreach email:** separate welcome/countdown/access flows and enablement controls.

There is no browser/OS/mobile push notification subscription implementation found in `frontend/src`. Closing the app does not leave the bell running as a phone push channel.

## Actual event/channel matrix

“No” means no automatic producer found for that event, not that a manager cannot manually compose a message. “Conditional” means a code path exists but requires configuration/consent/jobs; delivery is not asserted.

| Event | Landlord in-app | Tenant in-app | Automatic email | Automatic SMS/WhatsApp |
| --- | --- | --- | --- | --- |
| Confirmed rent payment, provider or manual | Yes; recent non-reversed receipts, seven days | Yes; own recent payment, 30 days | No | No |
| Payment reversed/corrected | Original disappears from payment alerts; no dedicated correction alert | Yes; own correction, 30 days | No | No |
| Collection pending/failed | Payment screen status; no dedicated bell event | Payment screen status; no dedicated bell event | No | No |
| New unpaid invoice | No separate new-invoice bell event; invoice screen | Yes; Invoice available | No immediate invoice-issued email; scheduled due reminder can send later | Scheduled due reminders only |
| Invoice overdue | Yes; mandatory arrears alert | Yes; mandatory arrears alert | Conditional tenant rent reminder | Conditional tenant rent reminder |
| Lease ending/expired | Yes; active lease within 30 days; renewal-in-progress excluded | Yes; own active lease within 30 days | No lease-expiry message producer | No |
| Renewal due to start but unsigned/unstarted | Yes; draft/pending-signature renewal whose start date has arrived | No dedicated matching renewal alert | No | No |
| Repair submitted/open | Yes; all open requests | Yes; own open requests | No | No |
| Repair scheduled/in progress | Open repair alert; landlord alert ID does not change with status | Yes; own current status/schedule changes alert ID | No | No |
| Repair completed/cancelled | Disappears from open-request bell; remains in maintenance history | Yes; own recently closed requests, 30 days | No | No |
| Repair comment | No dedicated new-comment bell event | Yes; recent non-internal comment by someone else, 30 days | No | No |
| Lease waiting for tenant signature | No dedicated signing-step bell event | Yes; own reachable agreement needing signature | Tenant invitation email only when email-link option selected | No |
| Lease fully signed | No dedicated completion bell event | Yes; own recently completed agreement, 30 days | Yes: signed PDF to tenant and landlord signer snapshot addresses, via outbox | No |
| Legacy collection-linked payout fails/needs review | Yes | No | No | No |
| Manual withdrawal successful | Yes; confirmed within seven days | Not applicable | No | No |
| Manual withdrawal failed/needs review | Yes | Not applicable | No | No |
| Landlord receiving account changed | No dedicated bell event | Not applicable | Email attempted to the user making the change | No |
| Mailbox verification request | Account flow | Account flow | Yes: verification link | No |
| Password reset request | Account flow | Account flow | Yes: generic recovery response, mail only for known active account | No |
| Tenant invitation | Manager invitation state | Invitation acceptance flow | Yes: invitation email when issued | No |
| Public lease verification code requested | Not applicable | Signing flow | Yes: short-lived email code via signing outbox | No |
| Identity check approved/rejected | Identity screen, not bell | Depends on account flow | Conditional email with a narrow SMTP/backend-name check | No |
| Beta welcome/countdown/access | Admin/applicant workflow | Not applicable | Conditional separate beta-email workflow | No |
| Manager explicitly sends a notice | Communication preview/history | External recipient message; no bell entry created just by sending | Conditional if email chosen | Conditional if channel chosen |
| WhatsApp proof submitted / approval requested | Proposed only | Proposed only | Proposed only | Proposed only; architecture draft is not implementation |

The notification API bounds individual source queries (100 per source). Tenant combined feed is capped at 200 and prioritises overdue alerts. A bell item can disappear when its underlying condition ends, even if it was unread. The manager feed is sorted oldest/date-first; it is not a complete permanent activity history.

## When the bell updates

`frontend/src/shared/components/NotificationBell.jsx` uses `useNotificationsQuery`:

- Manager poll: approximately every 60 seconds while the query is active.
- Tenant poll: approximately every five minutes while active.
- Several relevant application mutations invalidate notification queries, allowing earlier updates; query lifecycle/focus can also refetch. Do not promise a fixed delivery SLA or continuous background polling.
- Bell requires verified account access and an unsuspended workspace. It is shown to managers/tenants and admins acting in a workspace, not as a general standalone platform-admin incident feed.
- In-app payment, payout, lease and maintenance preferences filter categories; overdue alerts remain mandatory.

Consequences: a payment can already be recorded while another user's bell still awaits refetch. Read/unread is personal. Manager repair IDs omit status and comment IDs, so reading an open repair once can leave it read after later progress/comments; the tenant feed handles these changes more explicitly.

## When external rent reminders go out

`notifications/messaging.py` schedules only unpaid, active invoices belonging to active tenants. With the default reminder schedule it targets:

1. Three days before the due date.
2. The due date.
3. Three days overdue.
4. Six days overdue.
5. Nine days overdue.

Defaults: workspace local hour 09:00; platform quiet hours 20:00–07:00. Schedule settings can change the lead days, hour and repeat interval/count (up to three overdue repeats). This is a due-date schedule, not “email immediately when any invoice is created.” An invoice missing the configured reminder date does not imply a historical reminder catch-up campaign.

Every connected, workspace-enabled channel is considered. Email + SMS + WhatsApp can all be selected: this is a fan-out, not an automatic fallback preference. One invoice with all five dates and both paid channels could generate five SMS plus five WhatsApp messages, before SMS segmentation, additional invoices or manually composed notices. This matters when discussing eight credits.

Actual send gates:

- `messages` scheduler job enabled; registered cadence is every five minutes. Merely deploying `run_scheduler` is insufficient. Compose defaults omit `messages` for both test and production; an environment override or explicit command is needed.
- Global reminders switch enabled, workspace channel preference enabled and configured transport/runtime channel activation.
- Feature policy permits the channel; workspace, tenant and initiating manager (for composed messages) remain authorised.
- Current contact still matches, address is present, recipient preferences permit it and send restrictions/allowlists permit the destination.
- SMS/WhatsApp have exact-number consent. WhatsApp additionally needs approved template/language for rent reminders; composed free-form WhatsApp notices require an open service window.
- Quiet hours and SMTP quotas can defer delivery. Stale/paid reminders, changed recipients, removed permissions and other conditions can cancel/hold the message.

Most controls default off. Last recorded test-environment review on 2026-10-28 reported messaging email/SMS/WhatsApp and beta email switches off, with email recipient protection preserved. That dated observation does not establish today's production state or prove account/security email is globally off; those use separate paths.

Current general messaging sends are conservative: uncertain network outcomes go to needs-review; they are not blindly retried. Delivered/read receipts are supported for phone channels. Provider acceptance is not proof of inbox delivery. The signing outbox has its own bounded retries (maximum five attempts), expiries and worker loop, deployed separately from the messages scheduler.

## What Claude's eight message credits mean

Source: `docs/SUBSCRIPTION_PLAN_PROPOSAL_2026_10_26.md`, tier table and “Message credits” paragraph. This is a proposed commercial allowance; not an implemented ledger or approved final charging rule.

- Starter/Standard: proposed six credits per **leased unit** per month.
- Professional/Portfolio: proposed eight credits per **leased unit** per month.
- One SMS segment or one WhatsApp message counts as one credit in that draft.
- Credits pool at workspace level and reset monthly; they are not eight total messages for the entire landlord account and not eight per tenant independently.
- Email and in-app alerts do not consume credits.
- Proposed top-up: 100 credits for K40; proposed trial: 50 total credits. Both remain proposals.

Example under the draft's wording: 50 leased units on Professional would produce 400 monthly credits for the workspace. A one-segment SMS to 50 tenants uses 50 credits; a second WhatsApp message to those same tenants uses another 50. Long/Unicode SMS can consume several segments/credits. Sending to a manager is another recipient, not included for free within the tenant's message.

The document now prices subscriptions by **purchased unit capacity**, following the user's 31 October decision, but the credit row still says **leased unit**. This is unresolved, not permission to silently change the allowance. If credits follow purchased capacity, 50 purchased slots would grant 400 at eight per slot even when only 30 are leased; if they follow leases, the same workspace would grant 240. Confirm and update the draft before presenting it as a product promise.

No monthly grants/deductions/top-ups/credit wallet model were found in `apps/subscriptions` or `apps/notifications`. Existing send budgets and email throttles control provider volume; they are not a customer credit balance. No current eight-message limit is being enforced.

## Credit limitations exposed by this audit

The eight-credit figure is a pricing-budget idea, not a map of eight existing automatic notification events. Existing reminder settings alone can exceed it when multiple paid channels are enabled.

The draft's “at most K1.92” comes from eight times the worksheet's K0.24 SMS estimate. It is not a universal ceiling: WhatsApp categories have different costs, SMS segmentation varies, tariffs/taxes/provider markup can change, and the worksheet explicitly labels its WhatsApp figures provisional. Do not treat those figures as a current Zambia quote.

Meta's current official [pricing overview](https://whatsappbusiness.com/products/platform-pricing/) says charges depend on recipient market/category and delivered messages; service replies within a user's 24-hour window are free of Meta message charges, as are qualifying utility replies. A whole WhatsApp conversation is therefore not automatically billable once per incoming/outgoing bubble. Provider-specific charges can differ.

Before implementing credits, agree:

- Whether the allowance follows capacity or leases, which recipients count and whether paid-channel reminders fan out or use a chosen primary channel.
- Whether free service replies/incoming messages consume any customer allowance. Recommendation: do not charge incoming messages, free bot prompts, failed-before-billable sends or technical duplicate retries; keep account/security emails outside credits.
- How SMS segment count and provider billing events are reconciled. Reserve allowance before sending, settle against billable outcomes and reconcile unknown outcomes without double deduction; do not equate every generic send attempt with a charge.
- Whether WhatsApp credit weight varies by approved category or marketing is excluded from the initial shared allowance. One fixed credit across different prices needs deliberate pricing, not an assumed cost equivalence.
- What happens at zero credits. Recommendation: hold optional paid outreach, keep in-app/email essentials and rent checkout/confirmation usable, show the manager the fallback, and never leave a tenant's submitted claim inaccessible because paid notifications ran out.
- Rollovers, annual-plan monthly resets, top-up expiry, refunds and cost visibility. Current draft only states monthly reset/pooling, not all these edge cases.

## Gaps and the smallest sensible next changes

These are coverage findings and recommendations, not authorization to implement.

| Priority | Gap | Reason and minimal remedy |
| --- | --- | --- |
| First | No landlord payment-success email; no tenant emailed confirmation/receipt | Bell is derived from records and billing never enqueues transactional mail. Add one deduplicated event after confirmed payment, with actor/tenant/manager recipient rules and existing receipt access. No mail for an unverified screenshot or pending checkout. |
| First | No external notice of new repair or tenant-facing repair progress | Maintenance updates records/comments without outgoing jobs. Enqueue new-request mail to the chosen manager and meaningful visible progress to the tenant, excluding internal notes. |
| First | Reminder code can be configured but not run | Enable/verify the existing `messages` scheduler job only after transport, recipient controls and test delivery are ready. Do not add a second scheduler. |
| First | Existing dispatcher is tenant-recipient oriented | `MessageDelivery.tenant` is required and contact/preferences checks use that tenant. Extend explicit recipient roles and purpose as identified in the WhatsApp architecture before using this queue for manager messages. |
| Next | Withdrawal failure/review/success only in bell | Funds access should reach the manager outside the app. Add durable email, optional approved WhatsApp later, keyed to a real status transition. |
| Next | No immediate invoice-issued or lease-expiry email | Due reminders/signing email cover narrower triggers. Add explicit invoice-issued mail and scheduled lease-expiry notifications using shared domain events, respecting preferences and duplicate suppression. |
| Next | Manager misses repair comments and completed/corrected history in bell | Manager feed models current conditions rather than update events. Add bounded version/event keys for material changes and a durable delivery intent for external notifications. |
| Next | Identity result email has a narrow backend-name condition | Inspect/replace the SMTP-string gate with existing transport-readiness abstraction; validate both supported email routing modes. Currently cannot promise every decision sends mail. |
| Later | Failed payment, vacancy, manager summary and advanced alerts not covered | Decide useful audience/action first. Autopay alerts are premature because autopay is deferred; dashboard data alone is not an outgoing notification trigger. |
| Later | Browser/mobile push absent | Separate feature; email and optional WhatsApp can address away-from-app needs first without introducing push infrastructure. |

Settings currently expose channels/categories more broadly than actual outgoing event coverage. A saved email preference expresses willingness to receive supported messages; it does not mean every checked category has an email producer. UI copy should say which events each channel actually supports.

For implementation, prefer a small shared transactional event/outbox adapter with existing SMTP and messaging workers. Key deliveries by event + recipient + channel; only enqueue after domain success, preserve delivery failures separately from financial state, and retain the existing distinction between account/security mail and optional paid outreach. Do not build a new universal notification platform to fill these gaps.

## Source map and review boundary

- Bell: `backend/apps/notifications/views.py`, `tenant_alerts.py`; frontend `shared/components/NotificationBell.jsx`, `Services/queries.js`.
- Reminder/message sending: notifications `models.py`, `messaging.py`, `phone_messaging.py`, `settings_views.py`, `provider_webhooks.py`, `management/commands/run_messages.py`.
- Scheduling and deployment: `backend/apps/scheduler/jobs.py`, `services.py`; `deploy/docker-compose.test.yml`, `docker-compose.prod.yml`.
- Account/security: `backend/apps/accounts/account_mail.py`, `email_verification.py`, `invitations.py`, `views.py`; `apps/payments/views.py::notify_destination_change`; `apps/audit/identity_views.py`.
- Signing: `backend/apps/documents/signing.py`, `outbox.py`, `management/commands/run_signing_mailer.py`.
- Beta: `backend/apps/marketing/emails.py`, `views.py`; separate outreach flow.
- Commercial assumptions: `docs/SUBSCRIPTION_PLAN_PROPOSAL_2026_10_26.md`, `docs/OPERATING_COSTS_2026_10_26.md`.
- WhatsApp proposal: `docs/WHATSAPP_SELF_SERVICE_ARCHITECTURE_2026_10_31.md`.

No runtime tests needed for this read-only audit/documentation change. A future implementation needs backend event/recipient/permission/idempotency tests, shared suite checks, and configured synthetic delivery checks. Current source coverage, environment enablement and actual end-user inbox delivery must continue to be reported separately.
