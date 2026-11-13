# Messaging provider credentials

Super admins can replace Africa's Talking, Resend and Meta/WhatsApp credentials from Messaging settings. Environment values remain the initial source until a credential is replaced. No endpoint returns a saved secret or ciphertext.

## Security plan

- Store each replacement as authenticated ciphertext in a private PostgreSQL table. Bind the encrypted value to its credential name. Use a separate server-held Fernet key, with explicit fallback keys for encryption-key rotation; never derive this key from the application secret.
- Every replacement request includes the new values, current password and a current authenticator code. Re-read active superuser status and a confirmed authenticator under a short transaction. Consume the accepted TOTP counter once per user, so concurrent/replayed requests cannot reuse the same proof.
- Restrict the endpoint to platform superusers, validate an explicit credential allowlist, throttle writes, mark credentials as sensitive and return private/no-store metadata. Audit only credential names and actor identity. No provider network calls occur inside the transaction.
- Read replacements when an operation needs them, without a cross-request credential cache. Shared workers pick up replacements on their next operation. Keep provider/channel enablement and recipient consent as independent controls.
- Require both `APP_PROVIDER_CREDENTIALS_ENABLED=true` and a separately provisioned `PROVIDER_CREDENTIAL_ENCRYPTION_KEY`. Missing/invalid encryption configuration must fail closed when the store is enabled. Environment-only deployments retain their existing behavior when the feature is disabled.
- Add RLS and revoke Handy access for credentials and reauthentication state. Deployment must provision the restricted runtime policy after migration. Back up the encryption key separately from database backups; losing it makes replacements unreadable.

## SMS activation

Treat provider response codes 100, 101 and 102 as acceptance, not delivery. Preserve callback evidence for final delivery status. The provider's default sender is permitted only through an explicit TEST-only setting; production still requires an approved sender. Consent, opt-out, exact-number identity and send-time authorization remain mandatory.

## Validation

Cover anonymous/tenant/manager denial; active superuser access; missing authenticator, wrong password/code, expired/replayed code, concurrent changes, malformed/unknown fields, throttling, no plaintext response/audit/storage, encryption-key errors, field binding, environment fallback, and worker-visible replacement. Mock provider calls. Run SQLite and PostgreSQL suites, system/lint/migration checks, frontend build and browser replacement flows before TEST rollout.

## Operator setup and rollout

Provision a unique Fernet key in the protected environment as `PROVIDER_CREDENTIAL_ENCRYPTION_KEY` and enable `APP_PROVIDER_CREDENTIALS_ENABLED`. Deploy migrations and run `provision_runtime_database` with maintenance credentials before starting the restricted runtime. Preserve a protected backup of the encryption key independently of the database; never put it in source control. Existing provider environment keys remain in place until an admin replaces individual fields.

In Settings > Messaging > Provider credentials, choose Replace for one provider. Blank fields keep existing values. Submit the new credentials with the current account password and a fresh code from a confirmed authenticator. A code authorizes one replacement request; multiple fields may be replaced together. Old values cannot be revealed or downloaded. Confirm the account/environment and provider configuration before replacing a key: saving does not make a provider API call or validate account ownership.

For encryption-key rotation, install the new primary key and explicitly retain the previous key in `PROVIDER_CREDENTIAL_ENCRYPTION_KEY_FALLBACKS` until every saved credential has been re-encrypted or replaced. Losing the old key before that point prevents decryption. Do not disable the store as an automatic recovery mechanism: that would deliberately return to environment values.

TEST can use `APP_SMS_ALLOW_DEFAULT_SENDER=true` with an empty sender ID. This exception is ignored outside TEST. SMS activation also needs a callback token of at least 32 characters and the existing channel enablement setting. Configure the provider's delivery callback separately if final delivery receipts are required; acceptance alone is not handset delivery. Do not release held requests or create consent records during activation. Production activation and branded sender registration remain separate decisions.

## Local validation, 2026-11-13

- Full SQLite suite: 1,775 passed, 38 skipped. Normal-password-hasher security/SMS checks: 43 passed, 2 skipped. After splitting integration tests and batching readiness reads, focused final checks: 85 passed, 3 skipped.
- Django system checks, migration drift, Ruff and 23 deployment-policy tests passed. Frontend production build and all 50 Node checks passed.
- Real local browser: empty validation, masked keys, incorrect password rejection, successful replacement, code replay rejection, cleared form values and mutation variables, no browser-storage secrets, missing-authenticator gate, desktop/mobile and dark theme. No provider calls or real messages.
- With the store disabled, credential reads add no database queries. With it enabled, one or multiple requested credential names use one bounded lookup; readiness batches its secret reads. Saved values are read per operation, without a stale cross-request cache. The metadata endpoint loads names/timestamps only.
- PostgreSQL locking/RLS and full-suite results are recorded after completion below. Functional checks do not establish a broader load-capacity or production-readiness claim.

PostgreSQL validation: the initial full run passed 1,812 tests and found one new integration-fixture failure: the Resend path uses the separate `email_quota` connection, which that test had not declared. The fixture now uses transactional access to both database aliases and closes the mirror connection. The corrected PostgreSQL credential/runtime/email/SMS group passed all 102 tests, including concurrent replacement and RLS checks. The final tagged CI run is required to pass both complete database suites before TEST deployment.

Measured local enabled-store reads: six requested credential names use one query; metadata uses one query and excludes ciphertext. No external provider calls were used in these checks.
