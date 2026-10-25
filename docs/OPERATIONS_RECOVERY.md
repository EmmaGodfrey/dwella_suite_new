# Operations recovery

The scheduler runs explicit `APP_SCHEDULER_JOBS` only. Production enables beta
emails, daily media snapshots and hourly offsite backup copies; test enables
snapshots and backup copies. Automatic billing remains off. Test outbound email
is restricted by `APP_OUTBOUND_EMAIL_ALLOWLIST`, including the signing worker.

## Backups and retention

- The backup container writes a verified PostgreSQL custom dump and local media
  archive daily. Deployment also writes a dump before migrations; failure stops
  activation. Files are private to the application user.
- `snapshot_media` downloads private R2 objects into an independent local
  `media-r2-<date>.tar.gz` archive, with object names, sizes and SHA-256 hashes.
  It excludes `_backups/` and temporary `_healthchecks/` objects. A failed snapshot
  never replaces the last complete archive.
- Local retention is 14 days production / 7 days test. The hourly offsite job
  copies complete archives and dumps to `_backups/production/` or `_backups/test/`
  in that environment's private bucket, verifying downloaded SHA-256 hashes.
- Both R2 buckets have a 30-day object-expiry rule restricted to `_backups/`.
  Active media has no expiry rule. Existing multipart-abort rules are retained.

The local R2 archive protects against losing an individual cloud object or the
cloud bucket; the offsite dump protects against losing the server. The local
snapshot and offsite archive use the existing infrastructure and credentials.
They do not create a second cloud account or make backups immutable against a
compromise with access to both the server and the R2 account. Archive size grows
with retained daily snapshots; monitor disk and bucket usage.

Run commands from the deployed directory, replacing test with prod as needed:

```sh
docker compose --env-file .env.test -f deploy/docker-compose.test.yml exec -T scheduler python manage.py snapshot_media
docker compose --env-file .env.test -f deploy/docker-compose.test.yml exec -T scheduler python manage.py upload_backups
```

Inspect authenticated `/api/v1/platform/scheduler/status/` as a platform admin.
It exposes job histories, failures and worker heartbeat/counts without email
payloads or recipients. Container logs must not contain SDK credentials or
message bodies. A missing scheduler/worker heartbeat or failed backup needs
operator attention.

## Restore drills

Use an isolated PostgreSQL container/project with no exposed host ports. Restore
a real dump, check migrations/tables and record counts, and remove only that
isolated project afterward. Create any required external-tool roles as NOLOGIN
roles first; a database dump does not include cluster-wide role definitions or
passwords. A new production server needs its original role provisioning and
protected environment configuration too. Never restore over a live database
merely to test a backup.

For a real, explicitly approved database recovery:

```sh
deploy/restore-backup.sh test data/backups/db-YYYY-MM-DD.dump
```

The script validates the dump before stopping services, asks for `RESTORE`,
restores in a single transaction, and restarts backend, scheduler and signing
mailer on success or failure. Verify application health afterward. No unrelated
services are stopped. Failed preflight leaves the running services alone.

Verify an R2 media archive and restore into an empty directory:

```sh
docker compose --env-file .env.test -f deploy/docker-compose.test.yml exec -T scheduler python manage.py restore_media_snapshot /backups/media-r2-YYYY-MM-DD.tar.gz /tmp/media-recovery
```

The command validates all hashes before extraction, refuses existing contents,
links, traversal, duplicate or unlisted entries, and never changes R2. Restore
the selected recovered files to their original object keys using authenticated
S3 tools after reviewing the affected files. Preserve a copy of the damaged
state and pause upload writes while recovering. A drill uses a disposable object,
deletes it, recovers it from the archive, checks exact bytes, then cleans up.

## Signing outbox

Invitation, OTP and completed-copy intents commit with their signing state.
Their sensitive payloads use authenticated Fernet encryption with a key derived
from Django's secret; terminal entries wipe that payload. Drain pending entries
before secret rotation or configure Django `SECRET_KEY_FALLBACKS` to decrypt old
entries during rotation. Preserve protected application secrets when recovering
the database. Cryptography's Fernet/MultiFernet implementation is used rather
than custom encryption.

The `signing-mailer` service processes committed entries independently of long
backup jobs. Its claim/finalization transactions are short: no SMTP runs inside
a database transaction or signing-row lock. Delivery rechecks expiry, revocation,
current lease/signatory authority and the outbound recipient guard. Obsolete
intents are cancelled; transient failures retry at most five times with backoff.
Completed-copy failure leaves the signed document intact and the existing retry
action requeues it. API feedback distinguishes queued from delivered mail.

SMTP has no atomic commit with the database. A process crash after provider
acceptance and before recording success can cause a duplicate; stable Message-IDs
help identify the same intent but do not promise exactly-once delivery.

Manual bounded processing (no need to run alongside the worker normally):

```sh
docker compose --env-file .env.test -f deploy/docker-compose.test.yml exec -T backend python manage.py process_signing_emails --limit 20
```
