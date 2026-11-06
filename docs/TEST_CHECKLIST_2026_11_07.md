# Participant checklist in TEST

7 November 2026. Replaces the handbook as the participant-facing testing surface.
The existing app serves `/test/uat`; there is no new environment or service.

The checklist contains 131 current manager/tenant flows across 15 modules. The
catalogue excludes administrator workflows and includes customer-facing deposit,
renewal/end, identity-submission and optional assistant paths. Real gateway money
movement and SMS remain excluded; the payment-boundary check expects processing
to remain disabled. Scheduled renewal activation remains paused for this alpha.

## Interface

Modules start collapsed. Each flow has one result: Not tested, Passed, Partial,
Failed, Blocked or Not applicable. Instructions appear only under How to test.
Partial/failed/blocked results offer an optional note. Result changes save
immediately; notes have a Save note action. Failed requests keep the draft and
offer retry. Search, role and result filters keep the page short.

Testers sign in with their own email-verified accounts. Progress belongs to the
account and survives refresh; other participants cannot see it. The standalone
page also works after verification before business setup, or after tenancy access
is removed, without expanding access to business records. A Test checklist link
is present in the TEST sidebar. Open module/Open Dwella use the TEST base path.

Administrators see a read-only catalogue and Download tester results. The CSV
contains saved responses only, with participant email, flow, result, note, browser
and saved time. An optional email filter supports larger cohorts. Administrator
MFA is enforced and no administrator test cases are introduced.

## API and data limits

- `GET accounts/uat/`: static catalogue and own saved results; bounded by 131 cases.
- `PATCH accounts/uat/results/<case-id>/`: own result/note only; 240 writes/hour.
- `GET accounts/uat/export/`: platform administrators only; 30 exports/hour;
  at most 5,000 saved responses, filterable by tester email or ID.
- Every endpoint is restricted to explicit external testing in APP_ENVIRONMENT=test.
  Required mailbox proof, active identity and administrator MFA remain enforced.
- One current row per account/campaign/flow; notes are limited to 2,000 characters.
  Unknown flows/fields and invalid statuses are rejected. Field updates lock briefly
  and preserve simultaneous note/status changes. Unchanged saves do not rewrite rows.
- Responses are private/no-store. CSV text uses the shared formula-injection guard.
  Result reads have the same query count at one and 131 rows; exports use a single
  joined result query plus a bounded-count check, without per-response lookups.

The canonical catalogue is `backend/apps/accounts/uat_cases.json`; stable IDs are
used for saved progress. It is loaded once per process. Review changes to existing
flow meanings before reusing a campaign. The catalogue revision is returned with
the catalogue and export; it is not a financial/permission authority.

Migration accounts/0007 adds only participant results. TEST's existing maintenance
release step applies migrations and grants the restricted runtime role DML on the
new table. No provider configuration, payment services or participant records are
seeded by the feature. Human flows begin as Not tested; synthetic validation does
not pre-pass participant results.

## Validation

Django system checks, migration drift and Ruff passed. The complete local backend
suite passed 1,692 tests with 35 skips. The focused PostgreSQL
suite passed 113 tests, including simultaneous updates to one result. The TEST-base
production frontend build passed. Fifteen synthetic browser scenarios passed with
131 catalogue entries, covering saved results, notes/retry, participant separation,
filters, mobile/dark layouts, administrator read-only controls and CSV download.
These checks do not establish real inbox or WhatsApp handset delivery.
