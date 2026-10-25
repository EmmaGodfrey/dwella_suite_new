# Backup, recovery and signing delivery completion

Approved scope: operational items 1–4, 25 October 2026. Preserve the current UI
and signing authority checks. Release to test first, then production after the
checks pass. Do not start the deferred product modules.

1. Validate and release the existing scheduler, backup/restore, staging recipient
   restrictions and approved performance fixes. Verify real database restores
   in isolated PostgreSQL containers, never over an active environment.
2. Retain offsite backup objects for 30 days using rules restricted to
   `_backups/`; preserve unrelated lifecycle rules and active media.
3. Snapshot private R2 media into verified local archives (14 days production,
   7 days test), independent of R2. Include object names and SHA-256 hashes,
   exclude backup/probe prefixes, fail closed on incomplete downloads, and copy
   archives offsite. Restore only into an empty directory with traversal and
   checksum checks. Drill loss/recovery using disposable objects.
4. Persist signing email intents in the same transaction as their state changes.
   Encrypt invitation tokens and OTP payloads at rest. Claim outbox rows in short
   transactions; send outside all database transactions and signing locks.
   Recheck validity, expiry, tenant/workspace authority and recipient restrictions
   at delivery, cancel obsolete work, retry transient failures with a bounded
   schedule, and avoid resending a successfully recorded delivery.

Email acknowledgement and database commit cannot be atomic across SMTP: a
worker crash after provider acceptance and before recording success may produce
a duplicate email. The outbox must use stable Message-IDs and document this
limit; it must never promise exactly-once SMTP delivery. Prevent concurrent
workers from claiming the same live attempt, and do not resurrect expired OTPs.

Validation covers malformed/partial backups, same-size corruption, safe restore
paths, retries, stale/revoked invitations, hidden payloads, account/workspace
access, transaction rollback, competing PostgreSQL workers and slow SMTP while
signing rows remain writable. Run Django/Ruff/migration checks, the full backend
suite, PostgreSQL checks, frontend build and touched browser flows. Inspect live
job state, backup objects, restored hashes and health before reporting completion.
