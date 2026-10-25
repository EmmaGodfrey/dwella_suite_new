# Dwella Suite Agent Rules

## Shared Memory

Claude and Codex share one memory in `.agents/memory/` (gitignored: it holds personal notes and contacts, so never commit it or copy it into tracked files).

- At the start of every session in this folder, read `.agents/memory/MEMORY.md`, then open the files relevant to the request. Treat them as what was true when written; verify files, branches and commits before relying on them.
- After any meaningful chunk of work (feature, decision, outreach, plan), update the relevant memory file: what was done, where it lives, what is next. Use absolute dates.
- One topic per file, with frontmatter `name`, `description`, `type` (`user`, `feedback`, `project` or `reference`). Add one line per new file to `MEMORY.md`. Update an existing file instead of creating a duplicate, and delete memories that turn out to be wrong.
- Do not store what the repo already records (code structure, git history) or secrets such as passwords and API keys.

## Security Workflow

- Treat security-sensitive changes as plan -> implement -> validate work.
- When the runtime supports model selection, actually switch models for this workflow: use the strongest available model for planning, a slightly smaller but still capable model for implementation, then switch back to the strongest available model for final validation and review.
- If the runtime does not expose model switching, say so plainly and still follow the plan -> implement -> validate discipline.
- After validation, prepare the feature for commit and push, but let the user verify before pushing when they ask to review first.
- Commit messages must start with a bracketed change tag such as `[FEATURE]`, `[BUG FIX]`, `[IMPROVEMENT]`, `[SECURITY]`, `[DOCS]`, or `[CHORE]`.
- Add backend unit tests for every security behavior. Cover happy paths and meaningful failure paths such as validation errors, unauthenticated access, forbidden access, throttling, and malformed input.
- Prefer framework-native security primitives before adding new dependencies.
- Never weaken authentication, authorization, CSRF, CORS, cookie, password, or header settings without an explicit reason documented in the change.
- Validate user input in both frontend and backend. Frontend validation improves UX; backend validation is authoritative.
- Avoid user enumeration in account recovery flows. Responses for unknown emails should remain generic.
- Rate-limit auth, password reset, 2FA, and other abuse-prone endpoints.
- Use permanent email addresses for admin accounts. Block obvious disposable email providers, but treat email delivery verification as the real proof of ownership.
- Keep secrets in the root `.env`; never commit real secrets.

## Backend

- Work in `backend/`.
- Follow Django/DRF structure: model, migration, serializer, view, URL, test.
- Use managers/querysets when domain filtering becomes shared or non-trivial.
- API responses must use the standard envelope:
  `success`, `response_code`, `response_message`, `response_data`, and `pagination` for paginated list responses.
- Keep the centralized response renderer and exception handler as the source of truth for response shape.
- Run `python manage.py check`, `ruff check .`, and relevant `pytest` tests before finishing.
- For changes touching shared backend behavior, run the full backend test suite.

## Performance and Efficiency

- Treat query count, database round trips, memory use, external requests and persisted row growth as design constraints, not a later cleanup step.
- Measure representative hot paths before and after a change. For list endpoints, compare a small and a full page: query count must not grow once per returned row. Add query-count regression tests for confirmed bottlenecks.
- Read related data with deliberate `select_related`/`prefetch_related`, filtered annotations or bulk lookups. Do not issue ORM queries inside serializer methods or per-row validation/import loops when a bounded batch query can answer them.
- Push filtering, counts, sums and existence checks into the database. Avoid loading whole tables, histories, binary document payloads or unused model fields to compute a summary or render a list.
- Bound pagination, batch sizes, retries and worker run time. Avoid repeatedly scanning or downloading complete growing histories; incremental processing needs a durable cursor, overlap/deduplication and a recovery path.
- Keep transactions and row locks short and consistent in order. Never put network calls, SMTP, object storage, PDF rendering or other slow work inside a locked transaction without a documented necessity.
- Preserve financial correctness, tenant isolation and fresh authorization checks when optimizing. Never replace an exact monetary invariant with an unexplained tolerance or treat pending money as paid to save work.
- Use request-local reuse for repeated context reads; cross-request caches require explicit expiry/invalidation and must not become the authority for permissions or money.
- Retain meaningful financial/audit evidence without writing endless identical polling snapshots. Operational logs need a bounded retention policy; do not remove financial evidence as a performance shortcut.
- Prefer framework-native and existing infrastructure solutions. Do not add dependencies, services or broad caches without measured need. Run focused checks during implementation and the required full suite once the final shared changes are ready.
- During concurrent work, record ownership and leave another agent's active modules untouched. Separate audit findings from measured results, fixes and deferred work; passing functional tests alone is not a performance or production-readiness claim.

## Frontend

- Work in `frontend/`.
- Follow the React + TanStack Query data flow in `docs/FRONTEND_DATA_FLOW.md`.
- Use the purchased React template components as the first reference for dashboard UI.
- Keep API calls inside `src/Services/`; screens should use query/mutation hooks.
- Validate every user-facing form in the frontend while keeping backend validation authoritative.
- Before finishing frontend changes, run a production build and sanity-check the flows touched so we do not regress existing features.

## UI Skills

For frontend work, read the relevant project skill before editing:

- `.agents/skills/dwella-impeccable-ui/SKILL.md` for shaping, redesigning, critiquing, or polishing a complete surface.
- `.agents/skills/dwella-taste-ui/SKILL.md` for visual hierarchy, typography, spacing, color, card/border restraint, forms, and anti-generic review.
- `.agents/skills/dwella-design-engineering/SKILL.md` for motion, transitions, interaction feedback, and animation review.

Use only the skills relevant to the request. The product brief, existing Dwella design system, Fluent UI conventions, and explicit user direction take precedence. Playwright is optional and should be used only when browser-level visual or interaction validation materially improves confidence.
