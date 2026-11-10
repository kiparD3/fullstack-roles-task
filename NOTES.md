# Scope and verification

## Agreed behavior

- Keep `is_superuser` as the administrator flag. Add nullable manager/member roles; null falls back to member. Existing-user backfill is deferred to phase two.
- Managers can list users and view the metrics stub, but cannot modify other users or read their individual profiles. Members retain personal-profile and existing item-ownership behavior.
- Backend checks enforce permissions. Frontend controls consume current-user capabilities, fail closed, and distinguish unauthenticated 401 from forbidden 403 responses.
- Metrics are explicitly a stub. No global settings subsystem, policy engine or ADR framework is introduced.
- Frontend unit tests are deferred because no dedicated library is configured and no new dependency is being added. Playwright remains the browser/end-to-end test framework.
- Previously reported dependency advisories remain unresolved and outside this change. Deployment requires a separate dependency/security review.

## Verification — 10 November 2026

- Backend: 175 passing tests, including 71 database-independent unit tests and one migration integration test. The earlier count of 180 included five tests for the temporary seed script, which has been removed.
- Full Playwright Chromium suite: 78 passed, including inherited template tests and RBAC scenarios.
- Frontend TypeScript, Biome and production build passed; backend mypy, ty, Ruff and formatting passed. The ty check uses the project virtual environment.
- One upstream Starlette TestClient/httpx deprecation warning remains.
- Manual Chrome checks covered all four effective account cases during implementation. Final browser smoke checks reconfirmed admin controls and metrics navigation before teardown.

## Coverage

Measured using the existing coverage.py dependency with branch measurement and the full backend suite; this combines unit, API and integration tests.

- Changed executable backend application lines relative to the original baseline: 79/79 (100%). This counts executable added/modified lines from `git diff --unified=0` intersected with coverage.py's executed/missing lines, excluding tests, documentation and frontend files.
- Authorization rules, auth dependencies, models, metrics and the nullable-role migration: 100% measured coverage. Model coverage includes declarations; assertions separately check validation behavior.
- The migration integration test executes upgrade/downgrade in a rollback-only PostgreSQL schema, verifies existing users remain null, and checks the role constraint.
- Whole changed files include inherited branches: users route 99%, API router 92% combined coverage. Uncovered branches include inherited user-update paths and non-development private-router registration.
- Entire backend: 598/642 statements and 85/106 branches executed, or 91.31% combined coverage. This is not a claim of complete unit coverage or exhaustive behavioral correctness.
- Frontend unit coverage has not been measured. The 78 passing Playwright tests must not be described as unit tests.

## Development checkpoint

This commit restores the temporary seed, its five unit tests, custom local Compose/environment helpers and complete demo instructions. They are explicitly for disposable local development and are removed by the next cleanup commit. The permanent suite has 175 tests; this development checkpoint adds five seed tests. No dependencies changed.
