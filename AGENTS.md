# Dwella Suite Agent Rules

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

## Frontend

- Work in `frontend/`.
- Follow the React + TanStack Query data flow in `docs/FRONTEND_DATA_FLOW.md`.
- Use the purchased React template components as the first reference for dashboard UI.
- Keep API calls inside `src/Services/`; screens should use query/mutation hooks.
- Validate every user-facing form in the frontend while keeping backend validation authoritative.
- Before finishing frontend changes, run a production build and sanity-check the flows touched so we do not regress existing features.
