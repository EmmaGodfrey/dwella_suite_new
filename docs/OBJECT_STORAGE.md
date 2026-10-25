# Private object storage

## Starting choice: Cloudflare R2 Standard

Prepared on 2026-10-25. R2 is S3-compatible and has a monthly free allowance of
10 GB-month storage, 1 million Class A and 10 million Class B requests. Above
that allowance Standard storage costs $0.015/GB-month, with separate request
charges and no download bandwidth charge. The allowance is per account, shared
by its buckets. Choose Standard, not Infrequent Access, for the free tier.

Sources: [R2 pricing](https://developers.cloudflare.com/r2/pricing/),
[S3 compatibility](https://developers.cloudflare.com/r2/api/s3/api/),
[bucket-scoped credentials](https://developers.cloudflare.com/r2/api/tokens/),
[Django storage options](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html).

## Current scope

`STORAGE_BACKEND=local` remains the default. Switching to `s3` moves new Django
FileField/ImageField uploads (avatars, business logos, property and maintenance
photos, identity documents) to the configured private bucket. No model migration
is required. Existing object names remain the database references.

Generated invoices, lease PDFs, signatures and signed originals currently use
database binary fields. They remain in PostgreSQL; this preparation does not
move them or change their signing/revision protections. Back them up with the
database. Redis document-page caching is independent of object storage.

## Account setup

1. Enable R2 in the Cloudflare account. Cloudflare may require billing details
   even when expected use fits the free allowance. Set usage/billing alerts.
2. Create separate private Standard buckets, e.g. `dwella-production-media` and
   `dwella-test-media`. Keep public access and `r2.dev` disabled. Pick the desired
   location/jurisdiction before creation.
3. Create separate Object Read & Write S3 credentials, each scoped only to its
   environment's bucket. Application credentials do not need account/bucket
   administration. Store credentials in protected server environment files;
   never in frontend variables, Git, logs, or shared memory.

## Server configuration

Set these in the environment's existing protected `.env.test` or `.env.prod`:

```dotenv
STORAGE_BACKEND=s3
STORAGE_S3_BUCKET=dwella-test-media
STORAGE_S3_ENDPOINT_URL=https://ACCOUNT_ID.r2.cloudflarestorage.com
STORAGE_S3_REGION=auto
STORAGE_S3_ACCESS_KEY=REPLACE_ON_SERVER
STORAGE_S3_SECRET_KEY=REPLACE_ON_SERVER
STORAGE_S3_URL_TTL=900
MEDIA_CSP_ORIGIN=https://ACCOUNT_ID.r2.cloudflarestorage.com
```

For a jurisdiction-specific bucket use the endpoint Cloudflare supplies.
The CSP value is one exact HTTPS origin, without trailing slash or wildcard.
Only image sources are extended. Static JS/CSS/fonts still use the existing
frontend/static setup. `MEDIA_URL` is retained for local rollback, but S3 URLs
come from the storage backend. Bucket files remain private; authorized API
responses generate 15-minute signed image links. Treat these links as temporary
bearer credentials. Identity document links are never serialized: the existing
staff-only, audited download endpoint opens the object on the server.

Uploads pass through Django, so no browser upload CORS policy is needed. If a
future browser feature fetches objects directly, add exact-origin GET CORS then;
do not enable public buckets as a workaround.

## Activation and verification

Enable test first. Before switching any environment with existing local uploads,
pause upload writes, make a verified media/database backup, copy local media to
the private bucket preserving every relative key, and compare file counts and
SHA-256 hashes. Keep the local files. Changing the setting does not migrate old
uploads and there is no automatic fallback for missing bucket objects.

From the deployment root, substitute `.env.prod` and `docker-compose.prod.yml`
for production after test verification:

```sh
docker compose --env-file .env.test -f deploy/docker-compose.test.yml run --rm --no-deps --entrypoint python backend manage.py check_object_storage --write
docker compose --env-file .env.test -f deploy/docker-compose.test.yml up -d --no-deps backend frontend
docker compose --env-file .env.test -f deploy/docker-compose.test.yml exec -T backend python manage.py check
```

The probe writes random bytes under `_healthchecks/`, reads them back, and
deletes only its own object. Without `--write`, it checks configuration without
remote operations. It never prints credentials or signed URLs.

Verify avatar/property/maintenance uploads and image display, staff identity
download (200), non-staff/anonymous refusal, and expiry of a copied signed image
URL. Confirm unsigned bucket GET is denied and frontend CSP contains the exact
endpoint origin. Keep production and test credentials isolated. Restart any
worker service that uses uploads when changing its environment too.

Rollback: pause writes, copy any newly uploaded objects back to local media
preserving keys, verify hashes, set `STORAGE_BACKEND=local`, clear
`MEDIA_CSP_ORIGIN`, and recreate backend/frontend. Do not delete either copy
until verification and the retention period are complete.

Live bucket connectivity, unsigned-access denial, and expiring downloads remain
activation checks until account credentials exist. Automated tests verify signed
URL generation, safe configuration, upload ACLs, probe cleanup, and access rules
without contacting an actual cloud account.

## Off-server backups

The `backup` service writes nightly database dumps and media archives to
`data/backups`, and every deployment adds a `pre-deploy-*.dump`. The scheduler's
`offsite_backups` job (on by default in production and staging) copies any file
not yet in the bucket to `_backups/production/` or `_backups/test/`, checking the
uploaded size. It uses `BACKUP_S3_*` when set, otherwise the environment's
`STORAGE_S3_*` bucket and credentials. The application never deletes backup
objects: add an R2 lifecycle rule on the `_backups/` prefix (e.g. delete after
30 days) for retention. Until credentials are set the job fails visibly in
`/api/v1/platform/scheduler/status/`.

Restore by downloading a dump from the bucket into `data/backups` and running
`deploy/restore-backup.sh prod|test <file>`.
