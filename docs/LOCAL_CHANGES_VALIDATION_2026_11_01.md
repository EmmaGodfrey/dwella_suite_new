# Local changes validation — 1 November 2026

The user authorized fresh validation, focused commits and publication of the local work to `origin/develop`. This is a branch publication, not a production or test deployment, provider activation, price launch or approval to implement the remaining proposals.

## Included work

- Previously committed beta access, assistant launcher, guided-tour review, recorded collections/statements and operational notification changes.
- Claude's explicit collection/payout/withdrawal notice helpers and regression tests. Queuing failures do not reverse a financial transition. Collection success is announced through the billing receipt; pending withdrawals do not produce progress email.
- Dated subscription/cost proposals, separate SMS/WhatsApp purchase planning, WhatsApp self-service architecture and tenancy operations planning. These documents do not implement billing, customer charges or the proposed workflows.
- Report behavior and measured query-budget documentation for the backend changes already committed locally.

The operational email switch still defaults off, and `operational_messages` must be explicitly included in the scheduler job list before reminder emails can dispatch. No environment, DNS, sender account, live messaging or money-transfer settings are changed by this publication. Actor fallback behavior is retained. Proposal prices and policy choices remain proposals unless separately approved.

## Verification

Fresh full SQLite and PostgreSQL backend suites are required, including the payment notices and consolidated migration. Frontend pure-function tests, production build, Django check, Ruff, migration consistency and diff whitespace checks are also required. Source fingerprints are recorded privately so code changes during validation cannot silently be included in the tested commit set.

Fresh results:

| Check | Result |
| --- | --- |
| Full SQLite backend suite | 1,206 passed, 25 PostgreSQL-specific skips |
| Full PostgreSQL backend suite | 1,231 passed |
| Frontend pure-function tests | 25 passed |
| Frontend production build | Passed; existing bundle-size advisory |
| Django system check | Passed |
| Ruff | Passed |
| Migration consistency | No changes detected |
| Diff whitespace and tested-source fingerprints | Passed |

Private evidence: `output/local-push-full-sqlite.log`, `output/local-push-full-postgres.log`, `output/local-push-frontend-tests.log`. PostgreSQL ran on an isolated loopback test instance and stopped after validation. Synthetic fixtures and mocked provider transports were used; no real messages or payments were initiated. These checks establish functional/regression coverage, not a penetration test or blanket production-security sign-off.

## Publication boundary

Push `develop` after the local checks pass. The GitHub workflow runs backend, PostgreSQL and frontend checks on branch pushes. Production deployment is restricted to `main`; staging deployment requires a `test-v*` tag. No such tag or main update is included. Shared agent memory, root environment files, credentials, local databases, private evidence and generated artifacts remain excluded from commits.
