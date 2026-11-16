# Invoice and receipt delivery

User direction, 16 November 2026: invoice-issued notices should include the invoice
PDF, and confirmed-payment notices should include the receipt PDF, by email and
opted-in WhatsApp. SMS links are deferred. This changes document delivery only;
it does not initiate, confirm or alter payments.

## Implementation and safeguards

`APP_NOTIFICATION_DOCUMENTS_ENABLED` controls the new behavior and defaults off.
The existing operational outbox, recipient selection, event deduplication and
uncertain-send handling remain authoritative. Sent notices are not replayed.

Email notices use the existing bounded PDF reader and renderer. The document is
scoped to the exact authorized target. After rendering, access, the destination
and the document fingerprint are checked again. Missing required document facts
produce the existing authenticated website link and an explicit attachment
unavailable explanation, rather than invented details.

WhatsApp uploads private PDF bytes to Meta and sends a media ID. It never publishes
a public document URL. Opt-in, the verified number, recipient preferences, current
property access, document corrections and channel availability are checked before
and after upload. Rendering and provider requests run outside row-locking
transactions. The chat window is checked again after upload.

Payment-proof receipt notices use the same upload path and retain their existing
deduplication against operational notices. Review, question and decline messages
are unchanged.

## WhatsApp template dependency

Within an active 24-hour chat window, the PDF can be sent as a document message.
Outside that window, document delivery requires approved utility templates:

- `dwella_invoice_document`, English, document header and five body parameters:
  recipient, workspace, invoice reference, total, due date.
- `dwella_receipt_document`, English, document header and four body parameters:
  recipient, workspace, amount, invoice reference.

Add approved names to `APP_APPROVED_WHATSAPP_TEMPLATES` only after confirming
provider approval and the header/body structure. Until then, the existing approved
text notice continues; untemplated media is never sent outside the chat window.

On 16 November, Meta rejected new template creation with HTTP 400, code 100,
subcode 3835016: the WhatsApp business account is restricted from creating a new
template. A synthetic sample PDF was uploaded for template submission; no customer
documents or messages were sent. The restriction must be resolved in the Meta
account before outside-window PDF delivery can be activated.

## Rollout

Run the notification regressions and complete backend suites, Django checks, Ruff
and migration consistency checks. Release the tested code through the normal CI
gates, then enable the document flag deliberately. Keep production SMS disabled
until the approved sender ID is configured. Do not replay old notices or copy TEST
phone bindings into production.
