# Settings, transactions and communications

2026-10-26. User requested a platform transaction view with saved gateway responses, a single Settings destination for each role, and SMS/WhatsApp reminders. Layout proposals follow the existing Figma-first review preference. No application changes, provider account creation, credentials, live messages or transfers in this review.

## Implementation - 2026-10-26

**Follow-up:** send-only messages, scheduler, saveable unconnected channel choices
and Handy preview/confirmation are now implemented in
[COMMUNICATIONS_IMPLEMENTATION_2026_10_26.md](COMMUNICATIONS_IMPLEMENTATION_2026_10_26.md).
The bullets below describe the preceding Settings-only stage; in particular,
channel preferences are no longer rejected merely because delivery is unconnected.

The user approved implementation after the v2.1 review. Consolidated Settings and admin transaction browsing are implemented locally. The review history below describes the preceding design stage.

- `/settings` is the common destination, with role-specific tabs and URL-backed selection. Old Profile, Security, landlord Receiving Details, platform settings and Outreach Settings links redirect to the corresponding tab. The account menu now links to Settings; Billing and Outreach no longer expose separate configuration pages.
- Existing profile, identity, security, receiving-detail drawer, Outreach form and assistant controls are reused. Workspace contact and timezone preferences save through an allowlisted, workspace-scoped endpoint; currency stays read-only to preserve existing financial records.
- Personal in-app alert preferences affect the live notification feed. Overdue invoice notices stay visible. Workspace reminder schedules and platform quiet hours/spending limits persist with validation, throttling, private responses and audit records.
- Notifications has one Save action. Independently saved personal/workspace preferences report partial failure, preserve unsaved edits and retry only changes not yet saved.
- SMS, WhatsApp and automatic email reminders remain unavailable: no delivery service is connected for these reminder flows. Existing application email flows are unchanged. Saving preferences does not send messages, and the backend rejects attempts to enable unavailable delivery or fallback. Provider selection, actual sending workers, callbacks, consent activation and messaging delivery history remain subsequent integration work.
- Admin Transactions supports paginated collections, payouts and imported provider ledger records; bounded server search/status/environment/date filters; separate collection and payout fees; current-environment saved balance comparison; and linked transaction details. Saved redacted gateway requests/responses load only on demand and remain superuser-only and audited. Viewing/refreshing saved records never contacts Lenco or retries a transfer.
- Lenco remains the sole gateway. Provider routing, subscriptions, fees charged to users and SaaS prices are unchanged.

Deployment must apply `notifications.0002_messagingsettings_notificationpreferences_and_more`. No production database changes, provider account actions, live messages, charges, transfers, push or deployment were performed for this feature.

Validation: Django check and Ruff passed; migration drift check passed; production frontend build passed; 25 existing Node tests passed. The final full SQLite backend suite passed: 896 passed, 16 skipped. Synthetic browser flows cover saves, frontend validation, partial-save retry, old-link redirects, role tabs, on-demand evidence, Escape/close, and desktop/mobile/light/dark states without live API traffic. Query-count regression tests cover one versus twelve rows for all three new lists, with encrypted evidence omitted from metadata reads; this is not a large-history latency benchmark or a general production-readiness claim.

Browser review artifacts are private under `output/playwright/settings-*.png`; the replay script is `output/settings-browser.js`.

## Review

[Review entry](https://www.figma.com/design/aHlQPzHBsvGR4rNoabRQyW/?node-id=234-106).

| Proposal | Figma node |
| --- | --- |
| Landlord Settings / Billing | 234:111 |
| Landlord Settings / Notifications | 234:241 |
| Admin Settings / Messaging | 234:393 |
| Admin Transactions | 234:557 |
| Admin Settings / Payments | 234:702 |
| Transaction / gateway-response drawer | 234:832 |
| Mobile Billing settings | 234:863 |
| Mobile Notifications settings | 234:910 |
| Remaining settings / migration map | 234:979 |

### v2 revision (Claude, 2026-10-26)

After review, the frames were revised in place and extended. Changes: white cards on the wash background, label/value rows with a 280px label column, underline tabs (horizontal scroll on mobile), Badge/Toggle instances for states, real example states instead of placeholder or builder copy, one save model per page (Notifications no longer mixes a schedule drawer with a page save), gear/money sidebar icons, and an exchange timeline with Request/Response tabs in the detail drawer.

| Added frame | Figma node |
| --- | --- |
| Landlord Settings / Account | 246:762 |
| Landlord Settings / Workspace | 246:962 |
| Landlord Settings / Security | 246:1151 |
| Admin Settings / Outreach | 246:15992 |
| Admin Settings / Assistant | 246:16217 |
| Admin Transactions / no results | 246:16530 |
| Tenant Settings / Notifications (mobile) | 246:16378 |
| Local components (Settings/Tab, Settings/Row variants, Transactions/Row, Transactions/Ledger row) | 241:481 |

### v2.1 — Codex review resolved (Claude, 2026-10-26)

Each finding was checked against code before changing Figma.

1. Outreach (246:15992) is now a form using the existing `OutreachSettings` fields only: sender display name, sender first name, signature, short signature, influencer offer, daily cap (1–25, default 10), send-from hour (08–16), send-until hour (09–17), pause switch, plus read-only server mailbox/enabled status. Role/job title and reply-to removed. Validation and save-failure state: 252:16696.
2. Messaging (234:393) sending controls now have inputs (quiet hours from/until, daily spending cap in ZMW), SMS fallback switch, a note explaining that a send that would exceed the cap is held, not sent, and listed as Held, and a single save bar.
3. Fees: Collections column is Collection fee. The drawer (234:832) shows environment, collected, collection fee, settled amount, payout amount, payout fee and fee payer separately; unreported values stay Unknown. Payout badges use the model's labels (Processing, Delivered, Needs reconciliation).
4. Identity copy (246:762) is now "Reviewed by Dwella to confirm who runs this workspace"; no payout gate implied.
5. Unsupported fields removed: password last-changed (246:1151) and date format (246:962).
6. No-results (246:16530) and load error (250:1499) are separate frames.

| v2.1 frame | Figma node |
| --- | --- |
| Admin Transactions / Payouts | 251:1324 |
| Admin Transactions / Gateway ledger (balance check + provider activity, unlinked rows) | 251:1672 |
| Mobile admin transactions list | 252:16378 |
| Mobile admin transaction detail (full-screen sheet) | 252:16544 |
| Outreach validation / save failure | 252:16696 |
| Admin Transactions / load error | 250:1499 |
| Dark references: Billing, Notifications, Collections, Ledger, drawer, mobile Notifications | 253:1879, 253:2024, 253:2238, 253:2728, 253:2491, 253:2600 |

Still not drawn: admin Account/Security and tenant Account/Security; reuse the landlord structures with role-appropriate wording.

All transaction examples and reminder schedules are illustrative. Provider names are recommendations, not a user selection. Existing receiving-details editing remains a drawer. Bank destinations, payout scheduling and subscriptions are not added by this reorganisation.

## Consolidation

Landlord Settings: Account, Workspace, Billing, Notifications, Security. Admin Settings: Account, Security, Payments, Messaging, Outreach, Assistant. Tenant Settings: Account, Notifications, Security. Only show role-relevant sections. The admin's personal notification preferences can live under Account; platform messaging controls remain separate.

| Current location | Destination / handling |
| --- | --- |
| `/profile` | Settings / Account; preserve profile, contact, photo and identity workflows |
| `/security` | Settings / Security; preserve existing email verification and 2FA flows |
| `/billing/receiving-details` and Billing receiving-details button | Settings / Billing; remove the standalone configuration page/button and redirect old links |
| Initial workspace setup | Keep first-run setup; place subsequent workspace contact/locale editing under Settings / Workspace |
| `/admin/settings` Handy availability | Admin Settings / Assistant |
| `/admin/outreach/settings` | Admin Settings / Outreach; remove Outreach's Settings tab, preserve sender identity, signature, offer, pause and sending limits |
| Provider connection/configuration | Admin Settings / Payments and Messaging |
| Reminder schedules and channels | Landlord Settings / Notifications; tenant consent/preferences remain personal |
| Invoice generation, recording payments, receipts | Stay in Billing: these are operational actions/records |
| Outreach sequences/templates, review, outbox | Stay in Outreach: operational campaign content and records |
| Beta invitation controls and delivery timeline | Stay with the applicant: operational records/actions; any future global configuration belongs in admin Settings |
| Transaction and gateway-response history | New Admin Transactions, independent of Settings |
| Messaging delivery history | Operational Messaging screen, linked from Settings |

Update navigation, account menus, internal links and tour targets together. Preserve redirects, query-string deep links, browser Back and role guards. Keep current security/backend validation and current test-only receiving-number bypass boundaries. Do not enable unsupported channels with cosmetic switches.

## Verified existing foundation

Payment APIs already expose admin-only collections, saved exchanges, audited exchange detail and balance comparison. `backend/apps/payments/views.py` uses `IsPlatformSuperuser`, no-store responses and `payment.evidence_viewed` audit events. `evidence.py` encrypts and redacts saved request/response payloads. Existing collection serialization includes a separate payout and receiving destination.

The UI needs to distinguish provider HTTP acceptance from business success, collection settlement and payout delivery. Opening a detail must read retained evidence, not initiate a provider request or retry a debit. Load response payloads only when explicitly opened; do not fetch encrypted evidence for every table row.

Existing notifications are derived in-app alerts and acknowledgement records. There is no SMS/WhatsApp sending worker or reminder-preference model in the inspected notifications app. Subscription feature keys exist, but do not imply an active connection.

## Transaction implementation requirements

- Paginated platform collection and payout lists with bounded server filters for reference, workspace, dates and status; show gateway/environment explicitly.
- Reuse and extend existing admin-only evidence APIs. Link collections and payouts without exposing evidence to landlords, tenants or ordinary staff.
- Show gross collection, actual collection fee/net settlement, payout amount/fee and each independent state when recorded. Missing fee information is unknown, not zero.
- Keep provider-ledger records distinguishable from Dwella invoice collections. Imported provider activity may have no associated invoice.
- Include response operation, timestamp, HTTP status, saved provider status/failure reason, request/response tabs and redacted JSON. Viewing remains audited; no secrets in lists or browser logs.
- Use `select_related`/bounded lookups, defer encrypted bodies on metadata lists, and measure query counts at small/full page sizes.

## Provider recommendation, pending selection

Recommended SMS: Africa's Talking. Its official bulk-SMS page lists Zambia all-network tiers K0.24, K0.21, K0.19 and K0.17, tied to spending bands. Confirm account-specific tariff, taxes, Airtel/MTN/Zamtel coverage, delivery receipts and Dwella sender registration before funding. Long/Unicode messages can incur multiple segments. The Zambia promotional page's K0.17 is not the entry-tier quote.

Recommended WhatsApp: direct Meta Cloud API, integrated into Dwella's own controls. Requires a Meta business portfolio, WhatsApp Business Account, business number, production credentials/billing and templates as applicable. Direct integration avoids Twilio's additional published US$0.005 per inbound/outbound WhatsApp message, but applicable Meta template charges still apply. Do not promise WhatsApp is free or quote an unverified Zambia template rate.

Sources checked 2026-10-26:

- https://africastalking.ug/sms/bulksms
- https://zambia.africastalking.com/
- https://www.postman.com/meta/whatsapp-business-platform/collection/wlk6lh4/whatsapp-cloud-api
- https://whatsappbusiness.com/products/platform-pricing/
- https://whatsappbusiness.com/policy/
- https://www.twilio.com/en-us/whatsapp/pricing

## Messaging implementation requirements

Plan, implement, then validate security-sensitive changes. Keep provider secrets in root `.env`, expose only readiness/status to the UI. Landlords cannot edit platform connections, bypass channel readiness or mark recipient consent on someone else's behalf.

Use durable bounded jobs, a unique reminder identity, a pre-submission claim, explicit provider message IDs and delivery events. Do not blindly retry an uncertain send. Resolve invoice balance, current tenant/workspace access, recipient preference and WhatsApp opt-in immediately before sending; stop reminders when invoices are paid/cancelled or tenancies change. Respect recipient opt-out, quiet hours, workspace timezone and daily/workspace/platform spending caps. A manager enabling WhatsApp does not establish tenant consent. Use approved WhatsApp templates for business-initiated reminders and outside the 24-hour service window.

Separate preferences for tenant reminders and manager's own alerts. Show queued, accepted, delivered, failed and unknown states accurately. Automatic SMS fallback is an explicit preference because it adds cost; do not silently send duplicate channels. Preview on-demand recipients/content/cost and require send confirmation. Setting a preference itself must not send a live message.

Verify webhook signatures/authenticity according to each chosen provider; bound payload size and event processing, deduplicate callbacks and avoid storing endless repeated status snapshots. Keep message bodies and recipient details out of routine logs. Add backend tests for authorization, tenant isolation, validation, consent, unavailable channels, rate limits, callback authenticity/replay, duplicate jobs, stale invoices and ambiguous provider submissions.

## Delivery sequence

1. Review the concrete layouts, then implement settings relocation and admin transaction browsing using existing APIs.
2. Confirm providers and implement connection readiness plus persisted preferences, with unavailable channels accurately disabled.
3. Configure accounts, sender identity and approved templates; implement and validate the sending worker, callbacks and delivery history.
4. Perform only explicitly authorized live-message tests. Run Django check, Ruff, focused tests, full backend suite for shared behavior, frontend build and bounded desktop/mobile/theme interaction validation.

No push or deployment is implied by this request.

## Codex review of v2 — 2026-10-26

Read-only review of the revised Figma frames, including desktop/mobile settings, tenant notification preferences, transactions, evidence drawer and empty/error states. No Figma or application edits in this review. The underline tabs, consistent field/value alignment, role separation and exchange timeline improve the original proposals.

Resolve before implementation:

1. **Outreach controls do not preserve the existing contract** (246:15992). The illustrated 40-email daily cap exceeds the backend's authoritative maximum of 25 (`backend/apps/outreach/serializers.py`). Sending window and sender first name are missing; role/job title and editable reply-to are not existing settings fields. Preserve current controls and limits unless separately changing the feature. Sender/signature/offer/limit values appear read-only although the page ends with Save changes; draw actual inputs or an explicit edit drawer.
2. **Messaging controls lack an editing path** (234:393). Quiet hours, daily spending cap, SMS fallback and reminder availability display values/badges without input controls, an Edit action or a save model. The spending cap also needs a currency and an explanation of what happens before a send that would exceed it.
3. **Financial labels need to distinguish both fees** (234:557, 234:832). Replace ambiguous Lenco fee with Collection fee in the collections view. In details, show collection fee, settled amount, payout amount and payout fee independently when known. A net payout amount does not establish who paid the outgoing transfer fee. Include gateway environment so sandbox/live evidence cannot be confused. Retain Unknown for unreported amounts.
4. **Identity wording adds an unimplemented requirement** (246:762). “Needed before payouts can be sent to you” asserts a payout gate not enforced by the inspected current payment path. Identity review, receiving-number ownership verification and provider requirements are separate. Align the wording with the actual enforced policy; do not introduce a new payout gate through a relocation.
5. **Remaining review coverage**: Payouts and Gateway ledger tab layouts, mobile transactions/detail drawer, dark theme and settings validation/save-failure states are not demonstrated in the reviewed set. These are completion gaps rather than reasons for another overall redesign. Admin/tenant Account and Security can reuse shared structures with role-appropriate wording.

Additional implementation note: password last-changed time and regional date-format selection are illustrated but not present as inspected account/organization fields. Supply authoritative data/support or omit those values; never populate them from the mockup. The no-results and load-error examples are alternative states and should never render together as they do on the combined review reference.

## Codex recheck of v2.1 - 2026-10-26

Inspected updated Outreach/Messaging controls, fee/environment details, identity copy, Payouts and Gateway ledger screens, mobile transaction list/detail, dark references and Outreach validation state. Previous substantive findings are resolved in the designs. No further layout redesign is needed. One small visual correction remains: dark desktop references retain the navy logo/wordmark, which is difficult to distinguish against the navy sidebar; use the existing reversed logo asset. This is a design review, not runtime validation or provider activation. No Figma or application edits made.

