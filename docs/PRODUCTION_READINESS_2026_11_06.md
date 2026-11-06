# Beta release preparation and security follow-up

6 November 2026. This records validated changes and operational limits; it is not a
production release approval. Companion feature handoff:
[WhatsApp onboarding and menus](WHATSAPP_ONBOARDING_AND_MENU_2026_11_06.md).

## Completed source changes

The backend uses Django 5.2.19 LTS, Django REST framework 3.18.3, Pillow 13.0.0 and
pytest 9.2.0. Validation used a separate environment; the existing development venv
was retained. A final audit of the complete upgraded environment reported no known
dependency vulnerabilities, including its updated pip. Docker already upgrades pip
before installing the pinned requirements.

The upgrade exposed two compatibility issues that were resolved without changing
the domain rules: explicitly retain `lease=None` for optional one-off invoices under
DRF conditional uniqueness validation, and patch the concrete cache backend in the
cache-eviction regression instead of Django's attribute-forwarding proxy.

References: [supported Django versions](https://www.djangoproject.com/download/),
[DRF releases](https://www.django-rest-framework.org/community/release-notes/),
[Pillow releases](https://pillow.readthedocs.io/en/stable/releasenotes/).

Native Django admin defaults closed outside debug and can be explicitly disabled
with `APP_NATIVE_ADMIN_ENABLED=false`. This boundary concerns backend `/admin/`;
the Dwella platform console remains available.

Production defaults to requiring administrator authenticator enrollment. A privileged
account without a confirmed authenticator can access its own account state,
verification, authenticator setup and logout; operational API access is blocked.
The frontend routes it to Settings → Security. Confirming administrator enrollment
revokes existing password-only API tokens, so the next login uses the normal password
and authenticator challenge. Required administrator MFA cannot be disabled through
the self-service endpoint. `APP_REQUIRE_ADMIN_MFA=true` explicitly enables the same
policy on TEST. CI uses the test environment, with dedicated tests enabling the
production policy and exercising real token authentication.

## Runtime database split

The runtime provisioner creates a distinct PostgreSQL login with no superuser,
database/role creation, replication, RLS bypass, inherited roles or application
object ownership. It grants required DML/sequence access and explicit runtime
policies on private RLS tables. It does not grant schema creation or modification of
`django_migrations`. Application tenant authorization remains authoritative; this
does not claim new tenant-level database row policies.

`python manage.py provision_runtime_database` runs through the maintenance connection
and reads the desired `APP_RUNTIME_DATABASE_URL` from the protected environment.
Passwords and SQL exception details are never printed. The runtime URL must use a
distinct `dwella_runtime` login, a strong URL-encoded password and the same database
host, port and name. Provisioning refuses an existing owner/inherited role or a
public schema granting CREATE to the runtime role.

For a controlled transition, retain the maintenance `DATABASE_URL` and set these in
the protected root environment:

```dotenv
APP_RUNTIME_ENV_FILE=../.env.runtime
APP_RUNTIME_DATABASE_URL=postgresql://dwella_runtime_test:URL_ENCODED_STRONG_PASSWORD@postgres:5432/DATABASE_NAME
```

`deploy/prepare-runtime-env.py` derives a root `.env.runtime` with mode 0600, replacing
the application database URL and removing maintenance/bootstrap database credentials.
App containers load this file. The separately selected `maintenance` Compose profile
retains the maintenance environment and performs migrations and role provisioning
after the pre-deployment dump. The backend then checks its restricted connection
instead of running migrations itself. Each later migration batch repeats provisioning
so newly private tables receive the explicit runtime policy.

The optional transition must be enabled deliberately. Existing environments without
these variables retain their current boot behavior; preparing the source does not
remove live database privileges. Test the transition first, retain the protected env
backup and dump, then verify backend/workers, private documents, portal isolation and
ledger operations before promoting it. Rollback restores the prior environment and
container configuration; it does not delete financial records.

## Governance and observability

The live GitHub configuration now requires a pull request to main, all four CI gates
(`backend`, `backend-postgres`, `frontend`, `runtime-policy`), an up-to-date base and
resolved conversations. Administrator enforcement is enabled; force pushes and branch
deletion are disabled.

The production environment requires the repository owner's manual deployment approval
and permits only protected branches. This single-operator configuration permits the
owner to approve their deployment; it does not claim independent peer review. No main
merge or production deployment was performed by configuring these protections.
References: [branch protection](https://docs.github.com/en/rest/branches/branch-protection),
[environment protection](https://docs.github.com/en/rest/deployments/environments).

`python manage.py check_release_readiness --require-whatsapp` provides bounded,
read-only administrator, DB-role, recent-backup and WhatsApp worker/template facts.
An incomplete dependency produces a failing exit status without changing settings.
It exposes no contacts, message bodies or credentials. The command cannot replace
host, provider-account or live handset acceptance checks.

The public uptime workflow checks the API, application and marketing website from
GitHub every ten minutes with bounded requests/retries. It becomes scheduled when
the workflow reaches the default branch. Actual notification delivery depends on
the owner's GitHub notification preferences; a tested external alert route and full
CPU/disk/exception monitoring are not claimed installed.

## Webmin SSH-only boundary

The user selected SSH tunnel access. The reviewed root tool is
`deploy/restrict-webmin.py`: it limits the listener and access list to 127.0.0.1,
removes additional listeners/discovery, preserves TLS/login settings, and starts a
five-minute rollback timer. Confirmation requires a fresh SSH connection; a file lock
serializes timer rollback and confirmation. An independently edited configuration is
not overwritten during rollback.

The user applied and confirmed the tool through legitimate interactive root access.
Post-change checks found only `127.0.0.1:10000`, an inactive rollback timer, a working
authenticated SSH forward and an unreachable public TCP port. The tool did not alter
SSH configuration, firewall rules or hosted applications. The old broad firewall
allow rule can be reviewed separately; there is no public Webmin listener behind it.

To use Webmin, keep a local forward open from a terminal:

```sh
ssh -N -L 127.0.0.1:11000:127.0.0.1:10000 USER@SERVER
```

Then visit `https://127.0.0.1:11000`. The existing Webmin TLS/login controls still apply.
Webmin's [listener implementation](https://github.com/webmin/webmin/blob/master/miniserv.pl)
is the source for the bind, additional-socket and discovery settings used by the tool.

## Validation and release boundary

- Frozen-source complete SQLite suite: **1,649 passed, 34 PostgreSQL-only skips**.
- Frozen-source complete PostgreSQL 17 suite: **1,683 passed**.
- Django check, Ruff, migration consistency and whitespace checks passed.
- Production frontend build, **45 Node checks** and **15 browser scenario groups** passed.
- **23 deployment/root-tool unit checks** passed; both real Compose files passed
  resolved runtime-policy checks in legacy and restricted configurations using only
  synthetic credentials. Restricted app configurations omit maintenance credentials.
- The restricted-role PostgreSQL regression exercised private records, invoice source,
  exact balances and recorded payment/receipt behavior, and denied table creation,
  trigger disabling, role creation and migration-record writes.
- Public HTTPS checks passed for all three production endpoints. This is a point-in-time
  result, not a capacity or continuous-monitoring claim.

The two pre-existing unrelated edits in billing/views.py and portal/tests.py were
excluded from frozen-source validation and all commits. No live money writes, provider
send activation, email rollout or parked K1 reconciliation was performed by these
preparation steps.

TEST release `test-v2026.11.06.4` (`02df3c3`) completed all four CI gates and staging
deployment successfully ([release run](https://github.com/EmmaGodfrey/dwella_suite_new/actions/runs/42261141201)).
Live source hashes matched, no migrations remained, and all ten TEST services were
running with configured health checks passing. Public TEST health and the deployed
website verification bundle passed checks. Native Django admin returned 404 directly
from the TEST backend; `/test/admin/` on the public frontend is a SPA fallback.

The five TEST app services were then recreated with a distinct restricted database
login and filtered credentials, after a protected database dump and environment backup.
The live privilege check passed, and container inspection confirmed maintenance and
bootstrap credentials were absent from all five services. Administrator MFA enforcement
is enabled on TEST, with one administrator still needing normal authenticator enrollment.
Both verified phone links, the two-phone allowlist and existing channel settings were
preserved. OTP remains off. All three WhatsApp worker heartbeats and the recent offsite
backup check passed. Read-only receipt and statement rendering also passed with the
restricted login. The 19 non-TEST container identities remained unchanged.

Open release dependencies: Meta authentication-template permission/approval for the
new code flow; actual code/exception-branch handset checks; administrator enrollment;
production restricted-role transition; remaining host firewall/reboot policy and
monitoring acceptance. Earlier findings about browser token lifetime/origin isolation
and stored authenticator seeds are not claimed resolved. Production requires a
separate approved promotion after these dependencies are assessed.
