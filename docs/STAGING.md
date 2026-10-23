# Staging Deployment

Dwella Suite staging is isolated from production:

| Environment | Frontend | API | Compose project | Server path |
| --- | --- | --- | --- | --- |
| Production | `app.dwella.properties` | `api.dwella.properties` | `dwella-suite` | `/home/emmanuel/apps/dwella-suite` |
| Staging | `app.dwella.properties/test/` | `app.dwella.properties/test/api/` | `dwella-suite-test` | `/home/emmanuel/apps/dwella-suite-test` |

Staging has independent PostgreSQL, Redis, static, and media volumes. It does
not run the beta mailer and its environment keeps beta email delivery disabled.
The existing `app.dwella.properties` DNS record and TLS certificate serve both
instances; host Nginx routes only the `/test/` prefix to staging.

## Deploying a tested develop commit

Ordinary pushes to `develop` never deploy. A staging deployment starts only
when an annotated tag matching `test-v*` is pushed. The workflow rejects a tag
whose commit is not contained in `origin/develop`.

```bash
git switch develop
git pull --ff-only origin develop
git tag -a test-v2026.10.23.1 -m "Deploy develop to Dwella staging"
git push origin test-v2026.10.23.1
```

Use a new tag for each deployment. Do not move or reuse deployment tags.

The GitHub `staging` environment requires these secrets:

- `STAGING_SSH_PRIVATE_KEY`
- `STAGING_SSH_KNOWN_HOSTS`
- `STAGING_SSH_HOST`
- `STAGING_SSH_USER`
- `STAGING_DEPLOY_PATH`

The server retains `.env.test` at the staging deployment path. Releases copy
that file forward, while the file itself remains excluded from Git.

## Database access for external tools

The staging PostgreSQL service has no directly published host port. The
`db-gateway` service is the only public database path: it exposes host
port `5433`, accepts connections only from `37.27.247.86`, and passes PostgreSQL
TLS through to the staging database. External tools use a separate provisioning
role that can create roles and grant read access but has no write privileges.
Never expose or reuse the Django application's database role.

The gateway uses host networking so its source-address allowlist sees the real
remote address. PostgreSQL is mapped only to `127.0.0.1:55432`; do not publish
that private port on a public interface.

The host firewall must permit the provider and no broader source range:

```bash
sudo ufw allow proto tcp from 37.27.247.86 to any port 5433 comment dwella-staging-db
```
