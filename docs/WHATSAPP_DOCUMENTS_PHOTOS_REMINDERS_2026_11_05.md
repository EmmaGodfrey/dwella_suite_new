# WhatsApp documents, repair photos and requested reminders

Implementation and handoff, 5 November 2026. User authorised these three remaining Codex
features. Claude's money mutations and payment-proof adapter remain separate.

1. Add requested invoice/receipt and current-month tenant statement PDFs to the
   existing reply outbox. Resolve records from a current ActorContext, render and
   upload outside transactions, then recheck identity, access and source content
   before sending the uploaded media ID. Bound rows, file size and daily requests.
   Do not create public URLs or a stored PDF version on every request.
2. Accept repair images only inside an explicitly selected tenant repair draft.
   Reuse the bounded media worker, restrict downloads to authorised current drafts,
   validate and re-encode photos, and require final confirmation. Persist photo
   storage outside locked transactions; stale or abandoned drafts are cleaned up.
3. Give managers a recipient/balance preview and explicit confirmation for one
   reminder. Reuse MessageDelivery, its template/consent/quiet-hour/kill switches
   and the existing per-invoice/local-day identity. Recheck current money and access
   at confirmation and dispatch. Apply a bounded request allowance.

Validation: focused positive and failure tests for access changes, cross-workspace
IDs, opt-out, binding changes, malformed/oversized media, duplicates, concurrent
processing and uncertain sends. Verify no render/network/storage under a row lock,
measure document read query costs, then run Django checks, Ruff and the full backend
suite plus affected PostgreSQL tests. No sending switches, real outbound messages,
push or deployment are authorised by this implementation request.

## Implemented behaviour

### Requested PDFs

Tenant and manager invoice/receipt views offer **Download PDF**. The tenant menu
also offers a current-month statement; multiple linked tenant accounts are chosen
on a paginated menu. Other statement periods remain available in Dwella.

The outbox stores a typed record reference and statement dates, not a PDF or public
file URL. At dispatch the worker resolves current access, reads a bounded source,
renders an in-memory PDF and uploads it to Meta. Before sending the media ID it
checks binding, workspace/record access, reply window and the complete document
source fingerprint again. Later corrections cancel a stale upload's send. Sending
uses a correlated document message with a safe generated filename. A timeout or
unknown provider outcome is review-only; it is not blindly retried.

Invoice copies reuse the existing invoice renderer and tenant-detail requirements.
Their footer says current ledger copy rather than inventing an archived version.
Receipt copies read the existing payment allocation function, including the split
between charges and deposit. Statements reuse TenantStatement's exact ledger rules,
including void/reversal exclusions, opening balances and negative credits.

Limits: 12 PDF requests per binding per rolling day, 100 invoice lines, 100 invoice
payments, 300 statement events, 50 output pages and 8 MB. Oversized or incomplete
documents produce an authenticated Dwella link instead of a false empty statement.
No new document version or permanent binary is persisted for each chat download.

Protocol reference: [Meta document-media object](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/types/DocumentMediaObject/).

### Repair photos

Photos are accepted only inside a tenant's explicitly selected repair draft.
The current question is reissued when a photo arrives, so entry-permission buttons
remain usable. A draft accepts up to eight photos and deduplicates repeated Meta
media references. The final summary shows the count and offers Confirm / Remove
photos / Cancel. Pending or rejected photos cannot be submitted silently; the draft
stays available for another confirmation or removal.

The media worker verifies current identity, membership, tenancy and draft before
fetching. Unexpected hosts, unsupported types, files over 8 MB, images over 40 MP
and malformed images are rejected. A PDF is refused from metadata before fetching
its bytes. Valid photos are oriented, resized and re-encoded as metadata-free JPEGs.
The storage write happens outside the inbox transaction. Confirmation inserts only
MaintenancePhoto references to already stored files, alongside the new repair.

Temporary pointers last at most two days. Cleanup locks and marks candidate rows
unavailable, then deletes storage outside the transaction; confirmation locks those
same rows before transferring ownership. Recently active fetches are not collected.
Media completion uses its claim timestamp so an old worker cannot overwrite a newer
attempt. Submitted photos remain attached to the repair after temporary cleanup.

Migration **notifications.0013_retain_media_cleanup_pointer** changes the media
binding to nullable SET_NULL. Deleting a user/link must retain the temporary storage
pointer for cleanup rather than orphaning the file. Unbound media cannot be fetched
or submitted. Do not reverse this migration while unbound rows remain: first finish
their file cleanup. No new table or general queue was added.

### Requested reminders

The manager menu offers **Send rent reminder**. It lists unpaid invoices in bounded
pages, then previews the tenant, number, invoice, current outstanding amount and due
date. **Queue reminder** is the explicit confirmation; it never means delivered.
Changing the balance or recipient between preview and confirmation requires another
confirmation. Opening-balance invoices are excluded.

This uses the existing MessageRequest/MessageDelivery pipeline, approved rent
template and per-invoice/local-day identity. An automatic or requested reminder
already present for that invoice today prevents another one. Each initiating manager
is limited to 10 requested reminders per rolling hour. No rent or payment is changed.

The recipient needs a current active tenant account/membership and exact verified
phone opt-in. Dispatch rechecks the original initiating binding and generation,
manager authority, recipient and current invoice before and after claiming. Partial
payments refresh the outgoing template balance; paid invoices, opt-outs, changed
contacts, revoked links and removed access prevent sending.

Quiet hours, feature and transport switches, allowlists, personal preferences,
template approval and the platform **reminders_enabled** switch still apply.
Workspace automatic scheduling preferences do not suppress an explicitly requested
reminder. An unconnected or paused channel may hold the queued notice; connecting a
channel does not silently release old holds. Existing history shows its outcome.

## Validation and release

- 45 new journey/security/regression cases cover requested PDFs, changed access during
  upload, corrupted references, uncertain sends, rate limits, bounded document reads,
  repair validation/storage/confirmation/cleanup and reminder confirmation/deduplication/
  consent/quiet-hour/approval/authority checks.
- Final frozen-source SQLite: **1,569 passed, 28 PostgreSQL-only skips**.
- Broader PostgreSQL notifications/documents/maintenance/reports baseline: **513 passed**.
  Final PostgreSQL WhatsApp regression: **127 passed**, including the last metadata
  rejection and strengthened foreign-record tests. Final backend source hashes match
  the frozen validation snapshot; the disposable PostgreSQL server is stopped.
- PDF source query counts are constant for small/full examples: invoice 6, receipt 4,
  statement 4. These are read-path measurements, not a production capacity claim.
- Django check, full Ruff, migration drift and whitespace checks passed. No frontend
  surface or API response envelope changed.

Local feature commits: `7b434bf` (PDFs), `4f893c8` (repair photos), `7a90af3`
(requested reminders). Exact source manifests and disposable validation logs live in
ignored `output/whatsapp-extensions/`. The original billing/views.py and portal/tests.py
working edits are preserved and excluded.

No live send, provider activation, push or deployment was performed. The next release
needs migration 0013, then the separately authorised handset pilot: reconnect the
opted-out phone, verify current Meta template approval/configuration, receive all
three PDF types, submit/reject/cancel repair photos, and queue one reminder while
checking STOP, changed access and duplicate suppression. This implementation does
not itself prove handset delivery or finalise production readiness.
