# Property manager and tenant flows, with WhatsApp at the centre

Date: 2026-11-01. Status: agreed direction from the user; delivery in progress.

## User decisions (1 Nov)

- Three roles only: super admin (the user), property manager (landlord) and tenant. The property manager's workspace issues invoices; no separate owner/agent issuer profile for now.
- ZRA Smart Invoice integration is at the very back of the backlog. Ordinary invoices stay; no fiscal work.
- Rent invoices are generated automatically from each lease ahead of the due day; managers can still issue them by hand.
- WhatsApp becomes central. Both tenants and property managers confirm their WhatsApp number. Everyone uses the same Dwella beta number to ask simple questions and do simple actions; property managers can create invoices for tenants from WhatsApp.
- Collections and payouts were tested by the user in test and work.

## Work items and owners

Payments-adjacent work is Claude's (see `.agents/memory/feedback-payments-owner.md`); Codex builds the rest and reviews Claude's payment work. Small focused commits; no push or deploy without the user.

| # | Item | Owner | Status |
| --- | --- | --- | --- |
| 1 | Automatic rent invoices (workspace on/off + days before due, default on / 7 days) | Claude | Built locally 1 Nov |
| 2 | Payment details printed on invoices (bank / mobile money set once in Settings → Billing, up to three, audited; "Pay online" line when collections are on) | Claude | Built locally 1 Nov |
| 3 | Required tenant details (name, phone, NRC/passport, TPIN; individual/company) + missing-details checklist | Codex | To start |
| 4 | Combined unit + tenant import (CSV/XLSX), existing tenancies with opening balances; remove unit floor area | Codex | To start |
| 5 | Deposits: request, collect (Dwella checkout or recorded), held balance, deductions with evidence, refund, renewal transfer | Claude | Built locally 1 Nov (evidence uploads next) |
| 6 | Move-out: notice, move-in/move-out condition with photos, tenant acknowledgement, deposit settlement hand-off | Codex | After 3 |
| 7 | Tenant reimbursement claims: tenant submits with receipt/photos; manager approves/partly/rejects; settlement recorded | Codex (claim flow) + Claude (settlement/ledger) | After 5 |
| 8 | Tenant account statement (invoices, payments, credits over a period, PDF) | Codex | Reuses reports work |
| 9 | Tenant gives notice / asks to renew from the portal; manager accepts into the existing Renew lease flow | Codex | After 6 |
| 10 | Credit notes / refunds and one payment across several invoices | Claude | Later |
| W | WhatsApp channel (below) | Codex foundation, Claude money actions | Starts now in parallel |

Frontend follows the 29 Oct Figma review set (page 280:5060) for items 3–7. **The user approved these designs on 1 Nov.**

## WhatsApp: one Dwella number for everyone

Builds on `docs/WHATSAPP_SELF_SERVICE_ARCHITECTURE_2026_10_31.md` (identity, inbox, retries, evidence rules stay as written) and the existing `CONNECT <code>` number verification in `apps/notifications/phone_links.py`.

### Number confirmation for both roles

- The existing Settings → Notifications → Connect WhatsApp flow already works for any signed-in user. Make it prominent: setup checklist step for managers, a step after accepting an invitation for tenants, and a banner until connected.
- Upgrade the verified link into an account binding (one active number per user) used for actions, not only notifications. Unlinking, number change, access removal or STOP revokes it.
- The tenant's profile phone and their mobile-money number are never treated as a verified WhatsApp binding.

### What people can do (first release, deterministic menus and buttons)

Every action re-checks the user's current role, workspace and record access, and anything that creates or changes a record ends with an explicit **Confirm** button.

Tenant:
- What do I owe? → open invoices and balance.
- Send me my latest invoice / receipt → PDF.
- Pay rent → Dwella checkout link for the chosen invoice.
- I've already paid → payment proof flow (architecture doc §4).
- Report a repair (with photos) and follow its status.

Property manager:
- **Create an invoice**: pick tenant (search by name/unit) → rent for a month or a one-off charge (description, amount) → due date → summary → Confirm. Uses the same `create_invoice` service and limits as the website; the tenant gets the normal invoice notice.
- Who owes me? → arrears summary by property.
- Send a reminder to a tenant (one tap, respects quiet hours and opt-outs).
- Confirm a tenant's payment proof (architecture doc §4–6).
- New repairs and their status; acknowledge a repair.

Not available from WhatsApp in the first release: withdrawals/payouts, bank or payout details, refunds, reversing payments, lease signing, deleting anything.

### Simple questions (Handy)

- First release: free text that matches no menu gets the menu plus a short help answer.
- Next: route free-text questions to Handy with the caller's verified identity and workspace, using the same restricted read access Handy already has. Handy may only *propose* one of the allowlisted actions above; Dwella still shows its own summary and Confirm button and runs the action itself. Handy never writes records directly and never sees messaging/verification tables.

### Platform rules that shape this

- One Dwella number (currently Meta's test number; a dedicated SIM before go-live). Business-initiated messages outside the 24-hour window need approved templates: invoice issued, rent reminder, payment received, payment proof to review, repair update, connect your WhatsApp.
- The test number only reaches the allowlisted numbers added in Meta; that is enough for the beta pilot with the user's own phones.
- Inbound webhook stays fast: verify, store the event, acknowledge; a worker does the conversation and sends replies.

### Delivery order for WhatsApp

1. Codex: binding + inbound inbox + conversation state + reply sender (buttons/lists), menu and "What do I owe / send my invoice" read-only actions for both roles. Tests with synthetic webhooks.
2. Claude: manager **Create invoice** and tenant **Pay rent** link; then payment proof submission + manager confirmation.
3. Codex: repairs over WhatsApp; reminders sent on demand.
4. Codex + Claude: Handy for free-text questions proposing allowlisted actions.
5. Templates submitted to Meta; allowlisted pilot on the test number; dedicated number before launch.

## Automatic invoices (item 1, done locally)

- `Organization.auto_invoice` (default on) and `invoice_lead_days` (default 7, 0–28), edited in Settings → Workspace → Rent invoices.
- `run_billing` (daily 06:00) calls `issue_upcoming_rent`: for this month and next month, a lease is billed once `today >= due day − lead days`; this month is always caught up. Existing duplicate protection means no month is billed twice, and hand-issued invoices count.
- Late fees still apply when automatic invoices are off.
- Release step: the `billing` job is not in either server's `APP_SCHEDULER_JOBS`. Add `billing` (and `renewals`) there when releasing; check the invoice notice email is enabled so tenants receive them.
- Known edge: a renewal that starts next month is billed on its start day (once it becomes active), not ahead.

## Deposits (item 5, built locally 1 Nov)

- `billing.DepositEntry` is an append-only ledger per lease (opening, collected, deduction, refund, transfer in/out); held = sum. `DepositDeduction` reserves money until applied (proposed → accepted/disputed → applied/withdrawn).
- Collected entries follow deposit invoices automatically from `refresh_totals` (payments settle rent/charges first, deposit last; reversals post a negative correction). Online Lenco payments and manual payments both work because both go through `record_payment`.
- Manager: Lease → **Security deposit** drawer (Figma 280:5335): request deposit (issues a deposit invoice for what is still missing), deposit already held, propose deduction, apply/withdraw (disputed needs a resolution note), record refund (cannot exceed available). Every write is audited.
- Tenant: My lease shows held/reserved/available, deductions with Accept / Dispute (dispute needs a reason), and history.
- Renewal carries the unreserved balance to the new lease once; a renewal deposit request asks only for the top-up.
- Not yet: photo/receipt evidence on deductions, tenant/manager notifications for deductions and refunds, applying a deduction to unpaid rent, and the deposit allocation table on receipts (Figma 284:521).
