# Invoice documents and lease signing

Approved design direction: 24 October 2026. Implementation follows the Figma document set, while preserving existing page structure. A product-wide completion/backlog review follows this feature.

## Implementation contract

1. Generate A4 PDFs on the server. Preview pages are rendered from the exact saved PDF used by Download. Keep paper white in either UI theme. Support flowing multi-page text and stable document references.
2. Store invoice snapshots, lease versions, signed outputs and original externally signed PDFs privately in the database; never expose them through public media paths. Organization-scoped authenticated endpoints protect management access.
3. Lease versions freeze their parties, financial terms, complete manager-supplied agreement wording and document digest. Agreement wording and signatory authority must be explicitly approved before issue. Figma's clause outlines are not production contract text.
4. A designated active property-manager account signs for the landlord. Platform/support users cannot impersonate that signatory. A tenant receives an expiring random link and verifies a code delivered to the lease's tenant email before accessing document contents or signing. Only hashes of link/session secrets and verification codes are stored. Invalid links/codes produce generic responses; challenges and verification are rate-limited.
5. Phone drawing and uploaded image/PDF signature selection both produce a reviewed PNG. The signer confirms identity, intent and the exact document digest before submission. The server revalidates the image, strips metadata and rejects blank, oversized or malformed images. No signature endpoint accepts an arbitrary signer role or substitute tenant email.
6. PDF uploads render in a bounded, timed subprocess, without active PDF content being embedded in generated documents. Preserve an externally signed PDF byte-for-byte as an original attachment, explicitly identified as uploaded rather than verified by Dwella.
7. Each signature preserves the document reviewed, resulting signed output/digest, signer, role, authentication method, consent and signing time. A document lock prevents duplicate/stale signatures; changed lease terms invalidate pending signing access and require a new version. Signing never activates the tenancy automatically.
8. Keep lease status/lifecycle separate from document status. A revoked or superseded invite cannot recover access using an old verification session. Workspace suspension and loss of signatory membership are rechecked at use time.

## Delivery and validation

Implement in focused increments: PDF/private version foundations; signing/domain services; protected/public APIs and security tests; document previews and phone/upload signing UI; browser validation and final product review. No deployment or sending live invitations is part of development verification.

Validate permission and organization boundaries, public disclosure, expired/revoked links, code attempts/throttles, signatory identity/authority, stale digests, duplicate signatures, changed terms, safe image/PDF processing, private downloads, immutable signed/original outputs and failure rollback. Run Django check, Ruff, relevant tests, full backend suite, migration consistency, frontend production build and real-browser flows against a scratch database.

ReportLab supplies flowing PDF layout; PDFium/pypdfium2 supplies raster previews and PDF-source signature selection. Preview controls and signing flows reuse Fluent and Dwella tokens. Drawn/uploaded electronic signatures are not claimed to be certificate-based digital signatures.

## Product review after delivery

The completed code review is recorded in [PRODUCT_STATUS_2026_10_24.md](PRODUCT_STATUS_2026_10_24.md). The guided tour is the next design task, rather than an unannounced addition to document signing.

## Delivered workflow

- Billing → invoice → **Preview invoice** creates or reuses a fixed invoice snapshot. It includes issuer/contact information, dates, billing period, recipient, premises, itemized amounts, recorded payments, totals, outstanding balance and payment-reference instructions. Long payment histories flow across pages. Internal notes are excluded. This is an ordinary invoice PDF; it does not claim ZRA fiscal certification.
- Lease detail retains Key terms and History. **Documents and signatures** adds document versions and original attachments below them. **Prepare agreement** collects the landlord's legal identity, an active designated signatory, complete approved wording, schedules and confirmation. The original lease status stays unchanged.
- The preview has a white A4 paper surface, shadow, page controls, fit/zoom and private PDF download. Both preview and download use the stored PDF. The paper stays white in dark mode.
- Managers can create a private signing link or explicitly email an invitation to the frozen tenant email. A new invitation revokes the previous one. Links expire after seven days; email codes expire after ten minutes and allow five failed attempts; verified browser sessions last at most twenty minutes and stay in memory.
- The designated manager signs using their account. The tenant verifies the fixed email, reviews the agreement, draws a signature or uploads an image/PDF, selects the page/region, checks the selected signature, types the document name and confirms intent. Signature placement is in the relevant execution field. Dwella trims blank margins and strips image metadata.
- Each signature retains the reviewed digest and resulting PDF revision. Stale submissions, duplicate roles, revoked/superseded links, changed parties/terms, inactive signatories and suspended workspaces are rejected. Fully signed versions remain immutable even if a later agreement is prepared.
- Completed copies are emailed after both signatures commit. Failed delivery leaves the signed document intact and offers a retry; successful delivery is not repeated by that retry. Already signed external PDFs are stored byte-for-byte and labelled as externally signed, unverified originals.
- Public signing requests omit account credentials/cookies and support context. Public entries do not load the assistant widget; entry from a tab that already loaded it forces a fresh document. Referrers are suppressed before assets load. Generated PDFs, original files and signature images have no public media URL.

## API map

All management endpoints require the existing workspace permissions. Public signing is a separate expiring email-verification grant, not a tenant portal login.

| Endpoint | Behavior |
| --- | --- |
| `POST /api/v1/billing/invoices/{id}/document/` | Generate/reuse invoice snapshot |
| `GET/POST /api/v1/documents/versions/` | List versions / prepare a lease version; filters `lease`, `invoice`, `kind` |
| `GET /api/v1/documents/versions/signers/` | Eligible designated manager accounts |
| `GET /api/v1/documents/versions/{id}/` | Metadata, current terms and signing record |
| `GET …/{id}/pdf/`, `GET …/{id}/page/?page=1&sha256=…` | Private stored PDF / raster preview bound to current digest |
| `GET …/{id}/signatures/{signature_id}/pdf/` | Retained intermediate signed revision |
| `POST …/{id}/invite/`, `sign/`, `revoke/`, `email-copies/` | Explicit signing lifecycle actions |
| `POST /api/v1/documents/versions/source-preview/` | Bounded image/PDF source preview |
| `GET/POST /api/v1/documents/originals/`, `GET …/{id}/pdf/` | List/attach/download preserved original |
| `POST /api/v1/signing/{token}/request-code/`, `verify/` | Generic challenge response / email verification |
| `GET …/{token}/document/`, `pdf/`, `page/` | Verified recipient review, with `X-Dwella-Signing-Session` |
| `POST …/{token}/source-preview/`, `sign/` | Verified recipient selection/signing |

## Runtime and validation notes

Apply the documents migration and install the pinned ReportLab/PDFium dependencies. Production invitations, verification codes and completed copies require configured email delivery using the existing email environment settings. Console/dummy backends cannot deliver signing mail and never print verification secrets. Local browser validation used a separate database and a file-based mail backend; no live recipient was contacted.

Source uploads are bounded to 4 MB, submitted signatures to 1 MB, images to eight million source pixels and 1,500 processed pixels per side. PDF sources are limited to 50 pages; generated PDFs to 50 pages/8 MB. PDF parsing/rendering runs in a child process with a ten-second wall timeout, plus CPU/memory limits on Linux. Documents and signature revisions are private database binary records: include them in database backup/capacity planning. They do not use the public media mount.

Validation: full SQLite suite 488 passed / two existing PostgreSQL-only skips before the final added document cases; full PostgreSQL suite 500 passed, including real competing requests. The expanded latest document suite additionally passes independently on SQLite and PostgreSQL. Django check, Ruff, migration consistency and frontend production build pass. Focused frontend tests and real-browser preparation, landlord drawing, tenant email verification/PDF crop/signing, completed download, original attachment, required errors, desktop/mobile/dark and narrow/short viewport checks pass. Existing bundle-size and framework warnings remain. No feature push or deployment was performed.
