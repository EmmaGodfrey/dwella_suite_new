# WhatsApp foundation — 4 November 2026

Implementation scope: verified actor binding, durable inbound inbox, bounded conversation worker, private reply outbox, deterministic tenant/manager menus, live balances, invoice/receipt selection, repair status/reporting, and an extension boundary for Claude's money actions. Existing notification sends remain separate. No production activation is implied.

Identity uses the existing signed-in CONNECT challenge and account-side completion. Action linking additionally requires mailbox proof and current tenant/manager access. Notification opt-in remains separate. STOP, disconnect, password/email change and fresh access denial invalidate action capabilities. An old notification consent alone never establishes action identity.

Webhook processing verifies signatures/business/number, normalises and deduplicates bounded events, applies immediate STOP, then acknowledges without sending or rendering documents. Each malformed individual message is quarantined without rolling back other valid messages. The worker serialises a binding's conversations in short transactions, commits replies before network I/O, and never blindly retries an uncertain send. Opaque menu choices use 192-bit random tokens with only their hashes in the active conversation; choices are replaced on each turn and bind the current actor, binding generation, conversation revision, workspace membership and expiry. All record reads and sends recheck live membership, mailbox proof, suspension, feature policy and tenant linkage.

Defaults are closed: APP_WHATSAPP_SELF_SERVICE_ENABLED=false. Existing WhatsApp transport runtime control and own-phone test allowlist still apply. Unknown senders receive connection instructions only within their own inbound window. Plain messages do not grant proactive consent. No LLM or additional service is required.

Retention: inbound content cleared after 30 days, provider-ID tombstones retained 90 days, terminal replies retained 90 days, expired conversation drafts cleared after seven days. Every cleanup is bounded. Repair attachments and PDF delivery use authenticated website fallbacks until their dedicated media adapter is available; do not imply a link is a WhatsApp PDF attachment.

Validation includes synthetic signed webhooks, identity/replay/STOP/isolation tests, query budgets, concurrency checks on PostgreSQL, full backend tests, Django/Ruff/migration checks, frontend production build and touched-flow checks. This session does not expose active-model switching; plan, implementation and validation use the current model.

Ownership: Codex owns notifications/whatsapp, phone-link integration, webhook integration and connection controls. Claude owns billing/payment actions and their conversation adapter. Pre-existing edits in billing/views.py and portal/tests.py are excluded from this work.

## Claude adapter contract

Register one adapter explicitly in application startup using `conversation.register_money_adapter(adapter)`. Do not discover code from user text. `adapter.start(ctx, conversation, intent, target)` starts `pay_rent` / `payment_proof` for tenants or `create_invoice` / `review_proof` for managers. Set `conversation.draft['intent']` to that allowlisted intent. Subsequent turns call `adapter.handle(ctx, conversation, payload, selected)` only after fresh authorisation. `selected` is `None` for plain text, otherwise a consumed opaque choice containing `action`, `target`, `page` and current membership metadata. `choice(conversation, title, action, target, member=ctx.membership)` creates buttons. Use `response(text, options, guards)` for the result; interactive bodies are capped at 1024 characters.

Both hooks execute in the inbox transaction under the binding/conversation lock. Use existing domain services, an explicit final Confirm choice and idempotent domain writes. Never perform provider requests, media downloads, SMTP, PDF generation or uploads inside these hooks. A duplicate provider event cannot invoke the hook twice. A stale/reused choice cannot invoke a domain action. BACK and CANCEL clear the draft; STOP and UNSUBSCRIBE (also "stop all" and "opt out") revoke the entire binding as opt-out words. SMS still treats CANCEL as an opt-out because it has no guided steps. Validation errors and unavailable records or workspaces return to an authorised menu. Identity or credential failures revoke the binding and offer reconnection.

ActorContext supplies the current user, membership, workspace, role and active tenant IDs. It never fabricates an HTTP request. Recheck domain-specific eligibility in your service. A hook that creates a delayed sensitive reply must supply a guard and matching live validation in `guards_current`; do not queue an unguarded financial snapshot. Transport timeout/malformed result/5xx becomes review and is not blindly resent. Callback status may advance before the send response; transport preserves it.

The foundation does not implement invoice creation, checkout or PDF attachment delivery; menus direct those to authenticated Dwella. Payment proof is implemented by the adapter described under "Payment proof flow" below. Invoice/receipt links open existing authorised document screens; they are not public document URLs or PDF attachments. Repair reporting accepts a 160-character title, up to 700 characters of details, explicit entry permission and a final Confirm. Photos are added in the existing Dwella repair screen. On-demand manager reminders and Handy remain subsequent plan items.

## Payment proof flow

`whatsapp/proof_flow.py` is the registered money adapter. All writes go through `billing/proofs.py`, the same code as the website. A proof never changes a balance until a manager confirms the money arrived.

Tenant sequence, started from the menu, by typing a shortcut such as POP or "I've paid", or by sending an image or PDF: invoice (skipped when only one is unpaid), amount, method, date, reference, files, review, Confirm. Bank transfer and mobile money need a file in this flow. Cheque needs a file or a reference. Cash needs neither. Drafts last 24 hours, and the final Confirm lasts 10 minutes. When a manager has asked a question, the tenant can answer it through the same steps, creating a new proof revision.

Manager sequence: the `dwella_payment_proof_review` template or the menu's Review payment proof opens the facts and files, then Confirm received, Not received (reason required), Ask for details (question required) or Back. The template's Not received and Ask for details buttons go straight to the reason or question. A repeat of a file already on another proof is flagged as a warning only.

Template buttons carry a 192-bit token, stored only as a hash, bound to the binding and generation and valid for 24 hours. Pressing Review proof changes nothing. An old button reports the proof's current state, and a new revision invalidates earlier buttons. Decisions from the website also queue the tenant outcome template.

Files: `inbox.py` keeps only Meta's media ID. `media.py` downloads a file only while it belongs to a linked sender's active draft, outside any row lock, refuses redirects and non-Meta hosts, verifies the digest, and applies the website's cleaning. Temporary copies are deleted on submission and otherwise within two days; a file whose draft is gone before download is never fetched. `evidence.py` sends the stored files to the reviewer immediately before the review message; a failure adds a warning to that message rather than blocking it.

Template sends in `notices.py` require a template listed in `APP_APPROVED_WHATSAPP_TEMPLATES`, the recipient's proactive opt-in, and a live recheck of the binding, access and proof revision. Other cases are cancelled with a recorded reason; the existing email and in-app notices still apply. Uncertain sends are never retried.

Required template list for this flow: `dwella_payment_proof_review:en`, `dwella_payment_received:en`, `dwella_payment_proof_declined:en`, `dwella_payment_proof_question:en`.

Pay rent replies with a link to the invoice in signed-in Dwella, choosing first when several are unpaid. No money, card or mobile-money detail passes through the chat. The website page decides which ways to pay are offered.

Known limits: the website has no payment-proof screens yet, so the API and WhatsApp are the only routes. All connected managers receive the review template, because no designated reviewer setting exists. Sending and receiving against Meta has been exercised only with synthetic webhooks and mocked provider calls, including button payloads, media download and evidence upload.

## Release and operations

Apply notification migrations `0010_whatsapp_self_service`, `0011_whatsapp_media` and `0012_whatsapp_proof_notices`. New tables have PostgreSQL RLS and Handy grants revoked. No existing notification consent is migrated into action authority. Connect again using Settings → Notifications: request a challenge with `actions=true`, send CONNECT from the exact number, then complete in the authenticated account. Optional proactive consent may stay false. Use DELETE `/notifications/phone-link/` to disconnect. Password, email and email-proof changes invalidate action bindings. Old events cannot cross a reconnection generation.

Enable `APP_WHATSAPP_SELF_SERVICE_ENABLED=true`, the existing runtime WhatsApp transport control, and the environment transport default as appropriate. Retain the test-only own-phone allowlist. Enable the `whatsapp` scheduler job or run `python manage.py run_whatsapp` from a dedicated bounded polling loop. A one-minute scheduler is sufficient for initial test validation but introduces up to one-minute reply latency. None of these switches are activated by this change.

Inbox processing handles at most 100 events / 20 seconds per call, with up to four attempts and 30/120/600-second backoff. Capture admits up to 120 inbound rows per phone per rolling day; replies are limited to 60 per linked phone and one connection instruction per unlinked phone per rolling day. Dispatch handles at most 50 replies / 30 seconds, with a 10-second per-request transport timeout. Expired sends are cancelled; uncertain sends are review-only. STOP cancels queued replies and invalidates active choices immediately; a network request already in flight cannot be recalled. No row lock spans network I/O.

Protocol reference: [Meta interactive objects](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/types/InteractiveObject/) and [Meta list-message endpoint](https://www.postman.com/meta/whatsapp-business-platform/request/r3ufenw/send-list-message). The adapter uses short opaque IDs and at most ten list rows.

## Final validation

2026-11-04, current shared workspace: full SQLite 1,351 passed / 28 PostgreSQL-only skips; full disposable PostgreSQL 17 suite 1,379 passed. The focused WhatsApp suite also passed with the normal password hasher (45 passed / three PostgreSQL-only skips). PostgreSQL exercises competing processors/senders on independent connections, no transaction held across provider I/O, and RLS on all four private tables. A callback racing the send response cannot regress a read receipt.

Full final suites use an ignored, guarded disposable-test settings module with Django's faster synthetic-account password hasher; native hashers remain readable. No application password settings change. This is [Django's documented test optimisation](https://docs.djangoproject.com/en/6.1/topics/testing/overview/#password-hashing), not a password-cost benchmark. The temporary PostgreSQL clusters listen only on loopback; their durability tuning applies only to disposable unit-test storage, not live databases. Interrupted exploratory/native-hasher runs are superseded by the completed final suites. All task PostgreSQL instances are stopped after validation.

Django check, Ruff, migration consistency and whitespace checks pass. The frontend production build and all 36 existing Node checks pass. Synthetic browser checks cover phone validation, declining proactive notifications while linking actions, account-side completion, disconnect and desktop/390px dark layouts. Balance aggregation measures one database query at both one and 13 invoices; this is a query-budget result, not a production capacity claim. Evidence is ignored under `output/whatsapp-flow/` (final `fast-sqlite.xml`, `postgres-fast/results.xml`, `release-focused.xml`, browser captures and source fingerprints).

Validation includes the existing unrelated billing-view/portal-test workspace edits; those files are preserved and excluded from this feature's commits. No live messages, charges, transfers, deployment, production changes or enablement were performed by this implementation. Reconnect the opted-out pilot phone after an authorised test release, then exercise the new menu end to end before wider activation.

## Recovery review completed 5 November 2026

Unavailable invoices, removed memberships, suspended workspaces and disabled features clear the draft and return to a currently authorised menu without revoking the phone identity. Credential changes still revoke it. Reconnect notices have a separate once-per-24-hour budget so earlier linked replies cannot suppress them. A sole eligible workspace opens directly; workspace options exclude unlinked tenant memberships and load access policies in a bounded batch.

STOP queues one fixed acknowledgement per phone per 24 hours after revocation. This is a deliberate, narrow exception to the opted-out reply block to confirm the user's action: it cannot carry account details, choices, evidence, workspace scope or binding credentials. Dispatch still checks the configured sender number, recipient allowlist, open reply window and absence of a new binding. Consent stays revoked. Reconnection or any altered acknowledgement cancels the reply.

Validation of the exact backend source snapshot: full SQLite suite 1,429 passed / 28 PostgreSQL-only skips; focused PostgreSQL suite 121 passed. Regression coverage includes recovery, credential revocation, reconnect budgets, STOP acknowledgement tampering and transport boundaries. Workspace-picker query count is constant between one and eight memberships. The suites use the disposable settings described above. Django check, Ruff, migration drift and whitespace checks pass. This remains local work; no deployment, activation or live message is implied.
