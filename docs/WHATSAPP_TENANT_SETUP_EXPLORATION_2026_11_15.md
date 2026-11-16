# WhatsApp tenant invitations, setup and document references

15 November 2026. Exploration and recommended behavior; no application changes, template submissions, messages or deployments made.

## What the tenant should experience

A tenant should be able to accept a property manager's invitation and activate WhatsApp service without first creating a password or navigating Dwella Settings. Confirm basic details inside WhatsApp. Where sensitive identity or tax details are required, open a short-lived secure Dwella form directly from the chat, without a prior website login. Website account access can be added separately later.

This would be a new access path. The existing email-invitation and verified-account path must remain intact while it is introduced; changing a checkbox cannot implement it safely.

## Current code, verified locally

| Area | Current behavior | Implication |
| --- | --- | --- |
| Tenant invitations | `backend/apps/accounts/invitations.py` emails a three-day invitation, requires a permanent email, asks new users for a password, and requires existing users to sign in. | No WhatsApp invitation or passwordless chat acceptance today. |
| Unknown WhatsApp sender | `backend/apps/notifications/whatsapp/worker.py` directs the sender to signed-in Dwella Settings. | No pre-account setup conversation exists. |
| Chat identity | `whatsapp/access.py` requires an active, non-admin, email-verified user and checks the password/email authorization stamp. `WhatsAppBinding` is one-to-one with that user. | Chat-only tenants need an explicitly designed identity model; never fake email verification or invent email addresses to satisfy the current checks. |
| Tenant records | `tenants/models.py` allows blank email and nullable account link; phone is unique within each workspace. | A manager can already hold a phone-only tenant record, but that does not grant chat access. |
| Multiple workspaces | Invitation acceptance rejects another active workspace membership. The WhatsApp menu already offers workspace switching. | Resolve the saved cross-workspace tenant-account gap before promising the same tenant easy access to multiple landlords. |
| Native WhatsApp forms | `whatsapp/inbox.py` accepts button/list replies, not Flow `nfm_reply`; `transport.py` sends text, lists, buttons and requested documents. | Meta Flows would need inbound, outbound and backend integration, not only a form definition. |
| Required document facts | `tenants/details.py` currently requires name, phone, TPIN, billing address, plus individual identity details or company/representative details. | Some incomplete tenants can use basic services but cannot receive a newly generated invoice PDF. These are current Dwella rules, not a determination of legal requirements. |

## Invoice and receipt numbers returned in WhatsApp

Keep the existing official numbers. Invoices use `INV-0001`; payment receipts use `RCT-0001`. `common/references.py` allocates the next number within the workspace; database constraints enforce uniqueness per workspace. Independent workspaces can legitimately have the same number. A number is a document label, never an authorization credential.

Currently `whatsapp/conversation.py` lists invoices and receipts using only their numbers. An invoice detail shows reference, total, balance, due date and a website link; a receipt shows its number, amount, paid date and a website link. Both offer a requested PDF. The receipt PDF source also contains the related invoice, premises, payment method and external payment reference, although the chat summary omits these.

Recommended presentation, using illustrative sample data:

```text
Kafue Ridge Properties
Invoice INV-0042
November rent · Flat B2
Total: ZMW 3,900.00
Paid: ZMW 1,000.00
Still due: ZMW 2,900.00
Due: 30 Nov 2026

[Download invoice] [Pay balance] [Main menu]
```

```text
Kafue Ridge Properties
Receipt RCT-0028
Payment received: ZMW 1,000.00
For invoice INV-0042 · Flat B2
Paid: 15 Nov 2026
Remaining on this invoice: ZMW 2,900.00

[Download receipt] [View invoice] [Main menu]
```

Use the existing, authoritative invoice and payment records. A receipt number confirms a recorded payment; it must not imply that the invoice is fully paid. A submitted payment screenshot/proof must say “Received for review” and must not be described as a receipt until approved/recorded through the existing payment service. Payment implementation remains with its established owner.

For lists, keep the number in the row title and add a short description with period/premises/amount; descriptions need explicit transport support because current choices only contain `id` and `title`. Typed `INV-0042` / `RCT-0028` retrieval is not currently implemented: add it only against the sender's selected workspace and authorized tenancy, with a generic unavailable response. Preserve opaque action tokens and UUID URLs internally. If a tenant has more than one workspace, choose the workspace before resolving a number. Do not expose NRC, TPIN, full account identifiers or another tenant's name in list descriptions.

## Recommended invitation and setup journey

1. Manager selects an existing tenant record and “Invite via WhatsApp”. Use the record's normalized phone and authorized workspace. Record appropriate recipient permission before business-initiated messaging; having a number on file alone is insufficient.
2. If there is no active user-message window, send an approved invitation template, subject to Meta's classification and approval. Suggested initial copy identifies the inviting manager and Dwella, with “Accept invitation” and “Not me”. Keep balances, unit details and documents out of this first message.
3. Tenant replies using the invitation action. Validate a one-use expiring invitation against the actual webhook sender, intended phone, workspace, tenant, and current manager authority. A forwarded token from a different number cannot accept. Do not offer a tenancy search by name, NRC, reference number or phone alone.
4. After that check, show the workspace and tenancy being joined, and ask the tenant to confirm or report a mismatch. Never let this flow change the assigned unit, rent, lease parties or financial records. Existing-account matches need proof of control of that account before merging/linking; matching a typed email is insufficient.
5. Ask for only missing basic information, prefilled where appropriate. Use buttons and short questions initially; optionally replace this presentation with Meta Flows later. Confirm corrections before writing. Keep optional future-notification consent separate from accepting access and from marketing.
6. Collect sensitive identity/tax identifiers only through a purpose-limited secure Dwella form. It opens from chat with an expiring, sender-bound authorization exchange and does not require a password or existing website session. Redeem to a short-lived setup-only session; redact tokens, disable third-party analytics/referrers, and never expose tenant data merely on a GET request. Higher-risk corrections or identity conflicts require additional proof/manager review. Return to WhatsApp on completion.
7. Show a concise confirmation and activate authorized tenant chat access: balances, invoices, receipts and repairs. Accepting an invitation does not sign a lease, make a payment, verify a tax ID with an issuer, or prove ownership of an email address.
8. Offer optional web access later through separately verified account enrollment. Losing/reassigning a phone must have a recovery and revocation process; ongoing chat access still needs fresh tenancy/workspace checks.

An alternative entry is a manager-shared QR or click-to-chat link with an invitation token: the tenant sends the first message to Dwella and enters the same guarded acceptance flow. That can avoid dependence on a business-initiated invitation template for the initial interaction, but it does not waive identity checks, future template rules or consent requirements. No generic link should activate whichever tenant happens to share the phone number.

## What Meta supports and where the boundary lies

Meta's [WhatsApp Flows product page](https://whatsappbusiness.com/products/whatsapp-flows/) confirms customized signups and forms inside WhatsApp. This supports the basic-detail collection experience; it does not automatically create or authenticate a Dwella account. A Flow submission is input to validate, not an authorization grant.

Meta's [Business Messaging Policy](https://whatsappbusiness.com/policy/), checked 15 November 2026 (page dated 23 September 2026), requires recipient permission and approved templates for business-initiated conversations. Free-form replies are allowed within 24 hours of the user's last message; outside that window use approved templates. A sent invitation by itself does not open the user-message window.

That same policy prohibits requesting or sharing full personal ID card numbers, financial account numbers and other sensitive identifiers. Accordingly, do not collect full NRC/passport numbers, TPIN or ID photos in chat or assume an embedded Flow exempts them. This prevents promising that every field required by today's Dwella invoice rules can be collected entirely inside WhatsApp. A secure form with no prior login is the practical compromise. Whether particular masked/structured documents may be sent needs a separate provider-policy check before expanding document delivery.

Existing notes record a Meta authentication-template permission failure on 6 November. That status was not rechecked live in this exploration. It should not be assumed resolved, or treated as proof that utility invitations/Flows are unavailable. Verify current WABA/phone/Flow/template eligibility before choosing a rollout path. An invitation template must not be used to disguise an authentication OTP template.

Meta's detailed developer Flow pages returned HTTP 429 during this research. High-level product and policy findings above were accessible. Native Flow component limits, account eligibility, encrypted endpoint requirements and exact API payloads still need verification against current developer documentation before implementation.

## Implementation order and acceptance criteria

### Conversation should be natural (15 November clarification)

User clarified that the intended experience is ordinary conversation, with Handy or a separate chatbot interpreting messages. Buttons/menus should be optional shortcuts, ambiguity resolution and explicit confirmations, not the primary way to ask for help. This returns to the existing 1 November plan (docs/FLOWS_AND_WHATSAPP_PLAN_2026_11_01.md, Simple questions/Handy); it is not implemented by today's menu engine.

Examples: “How much do I still owe?” -> exact authorized balance; “Send me the receipt for the thousand I paid yesterday” -> look up authorized payments, clarify if several match, send the requested receipt; “My kitchen tap is leaking” -> collect missing repair details conversationally, show summary and ask to submit; “I paid already” -> start the existing proof/review flow, never invent a paid status. Short-lived context must support follow-ups such as “the November one” without leaking between people, workspaces or tenancy changes.

Recommended structure: WhatsApp -> Dwella sender/tenancy checks -> conversational interpreter -> narrowly defined Dwella read/action tools -> authoritative result -> natural reply. Invite acceptance, account linking and sensitive-field collection retain their guarded state machines. The interpreter can propose an intent, ask a follow-up or phrase a result; it cannot choose its own identity/scope, authorize writes, execute SQL or invent figures/document references. Confirm consequential actions against a specific current draft; an ambiguous “yes” from an old conversation is insufficient. Existing cancellation, STOP, deduplication and worker limits remain authoritative. Tool results should include the facts needed for a complete answer without per-row database calls; bound model/tool rounds, history, timeouts and retries. Provide clear text/buttons and human support when the model is unavailable or uncertain.

Prefer reusing Handy if it exposes a supported server-to-server conversation API with tenant-scoped tools, acceptable latency/cost and controllable retention. The repository currently integrates a website widget and manager-only Handy grants: accounts/handy_agent.py has no tenant group, its action roles are landlord-only, and its token helper uses the ordinary web membership resolver. Do not grant tenants a manager token, reuse the manager-wide database policy, or assume the widget itself can be routed into WhatsApp. API capabilities and tenant support remain unverified. A separate lightweight conversational backend is a viable alternative behind the same Dwella tool interface; it should not duplicate the ledger, permissions or onboarding logic. The user has clarified the experience, not selected a new provider or authorized new tenant grants. Existing Handy Professional+ packaging also needs an explicit distinction between basic tenant WhatsApp service and premium manager assistant features.

First improve document reply copy and list context while preserving official numbers and current access checks. Next design the phone-first invitation identity and cross-workspace linking rules. Implement plain-chat acceptance/basic setup and the secure missing-details form; pilot on TEST with real invited handsets. Add native Flows once eligibility and a working fallback are verified.

Security-sensitive implementation must follow plan → implement → validate, including backend tests for sender/token mismatch, expiry, revoke/resend, replay and duplicate webhooks, throttling, forged buttons/Flow submissions, existing-account conflicts, cross-workspace isolation, wrong/stolen/reassigned phones, STOP, incomplete forms, concurrency, manager access removal and no accidental lease/payment writes. Runtime model switching is not exposed here; do not claim a separate-model security review occurred. No security code was changed in this exploration.

For document copy, verify partial payments, multiple receipts, reversed payments, void invoices, missing document facts, same numbers in different workspaces and per-row query counts. Any PDF-policy changes need their own review. No historical renumbering is proposed.
