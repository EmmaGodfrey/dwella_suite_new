# Tenant receipts and payment confirmation

2026-10-25: user requested better tenant receipts and visible feedback between
Lenco closing its window and Dwella confirming payment. Reuse the existing A4
receipt document for tenants/managers, including a separate print root so browser
Print / Save PDF shows only the receipt, not the app shell or a blank page.
Keep existing receipt amounts, dates, invoice allocation/balance, reversal states
and server access boundaries. Do not expose landlord payout details to tenants.

Show opening, hosted checkout, awaiting confirmation, delayed confirmation,
server-confirmed receipt, failure and review states in the invoice drawer.
Provider callback payloads never mark paid or alter balances. Callback event
names may guide UX, but server collection status and receipt remain authoritative.
Keep one existing pending-collection poll loop; no faster polling or duplicate
provider calls simply to animate progress. No fake percentages or success timer.

Payout is a separate issue: Lenco rejected the real user's automatic payout
because its API key lacked mobile-money transfer permission. User reports finding
and enabling that permission. Do not blindly resubmit the existing payout; it
remains in status-check mode pending controlled reconciliation/recovery. This
UI change does not make a live transfer or retry an outgoing debit.

Validation: frontend production build and 21 focused Node tests passed. Synthetic
browser checks held the verification request open to prove immediate feedback,
then exercised delayed confirmation and the server-confirmed receipt transition.
The existing poll interval remained unchanged (five collection reads in the
scenario). Mobile light/dark layouts had no horizontal overflow; Print / Save PDF
produced one A4 receipt page. Checkout and API responses were mocked, with no real
collection or payout initiated. Feedback uses the existing Fluent spinner and
static status text; no custom motion, fake progress or timed success transition.
