# Fullstack Roles Task

Phase-one RBAC implementation on the Full Stack FastAPI Template. Existing `is_superuser` behavior is preserved. The new nullable `role` stores `manager` or `member`; a null role has member permissions. Superusers always have admin permissions, regardless of `role`. Existing rows are **not backfilled**.

## Permissions

| Action | Admin (`is_superuser`) | Manager | Member / null role |
| --- | --- | --- | --- |
| List users | Yes | Yes | No |
| Create / edit / delete other users and change privileges | Yes | No | No |
| View metrics stub | Yes | Yes | No |
| View / update own profile | Yes | Yes | Yes |
| View another user's individual profile | Yes | No | No |
| Basic items features | Existing template behavior | Own items | Own items |

The existing settings page contains personal settings, so all roles retain access. No global settings subsystem was added. The existing protection against a superuser deleting themselves is retained.

## Authorization design

`backend/app/core/authorization.py` resolves effective roles and defines capabilities. FastAPI dependencies enforce permissions on the backend; existing superuser dependencies remain on administrative mutations. Every authenticated request loads the current database user, so privilege changes apply to existing tokens. Missing, invalid, expired, malformed-subject and deleted-user tokens return 401; inactive users and insufficient permissions return 403.

The current-user endpoint returns the effective role and capabilities. Frontend guards, navigation and administrative controls consume those capabilities rather than duplicating a role matrix. Guards wait for identity, fail closed on errors, and display a friendly forbidden state. API 403 responses preserve authentication; 401 responses end the session. Login/logout cancel requests and clear cached identity/data to prevent cross-account leaks.

Signup and self-profile schemas reject extra privilege fields. New registrations default to member. Admin forms may set manager/member or leave an account unassigned; the superuser checkbox still controls admin access. A database constraint allows only manager/member/null. Phase one adds the column without a default or backfill; data migration and a potential non-null constraint are deferred to phase two.

## Setup and tests

Use the original template's [development instructions](development.md) and committed lockfiles. Configure your own environment values. No demo account seed, custom local Compose stack, or credential-bearing environment helper is included in this feature.

Apply the schema migration through the normal backend prestart flow (`alembic upgrade head`). It adds a nullable role column without assigning roles to existing users. Existing superusers remain administrators and can assign roles through the Admin page.

Backend tests delete users/items from their configured database. Use a dedicated disposable test database, apply migrations to it first, and never point the suite at production or a database you want to preserve. With the required environment variables configured and `DATABASE_URL` pointing to that test database, run from `backend/`:

```bash
uv run alembic upgrade head
FASTAPI_ENV=development uv run coverage run --branch -m pytest tests/
uv run coverage report
# Unit tests override the database fixture and do not open a database.
uv run pytest tests/unit -q
uv run bash scripts/lint.sh
```

For browser tests, follow the frontend setup in [frontend/README.md](frontend/README.md). Start the backend, frontend and Mailpit with a separate disposable development database, configure `FIRST_SUPERUSER`, `FIRST_SUPERUSER_PASSWORD`, `VITE_API_URL` and `MAILPIT_HOST` for that environment, then run from `frontend/`:

```bash
bun x playwright install chromium
bun x playwright test --workers=2
bun run build
```

RBAC tests cover allowed/denied roles, null fallback, superuser precedence, ownership, escalation attempts, invalid roles, database constraints, expired/invalid credentials and role revocation with an existing token. Playwright adds real role sessions, navigation/direct-route checks, read-only managers, profile updates, identity loading/failure, API 403 handling and account switching. Existing template tests remain included.

Frontend unit tests are deferred in this phase: no dedicated frontend unit-test library is configured, and no dependency is being added. Playwright supplies browser/end-to-end tests, not frontend unit tests; frontend unit coverage is not measured.

Latest verification: **175 backend tests passed**, including **71 isolated unit tests** and a migration integration test; **78 Playwright tests passed**. All **79 added/changed executable backend application lines** were executed. Whole-application coverage is **91.31% combined statement/branch coverage**, including inherited template code. See [NOTES.md](NOTES.md) for scope and limitations. Execution coverage is not proof of exhaustive correctness.

Regenerate the API client after backend schema changes with `bash scripts/generate-client.sh` and the required environment configured.

## Deployment scope

Use the original [deployment instructions](deployment.md) with separate production data, credentials and configuration. Temporary accounts were for development testing only and must never be promoted to production. No development-only setting should be enabled in production. Previously reported dependency findings remain unresolved and outside this RBAC PR; this change is not a production security certification.

## Framework references

Implementation follows [FastAPI parameterized dependencies](https://fastapi.tiangolo.com/advanced/advanced-dependencies/), [TanStack Query cache management](https://tanstack.com/query/latest/docs/reference/QueryClient), and [Playwright isolated authentication](https://playwright.dev/docs/auth). These patterns were checked using Context7.

---

## Original template documentation

# Full Stack FastAPI Template

[![Test Docker Compose](../../actions/workflows/test-docker-compose.yml/badge.svg)](../../actions/workflows/test-docker-compose.yml)
[![Test Backend](../../actions/workflows/test-backend.yml/badge.svg)](../../actions/workflows/test-backend.yml)

## Technology Stack and Features

- ⚡ [**FastAPI**](https://fastapi.tiangolo.com) for the Python backend API.
  - 🧰 [SQLModel](https://sqlmodel.tiangolo.com) for the Python SQL database interactions (ORM).
  - 🔍 [Pydantic](https://docs.pydantic.dev), used by FastAPI, for the data validation and settings management.
  - 💾 [PostgreSQL](https://www.postgresql.org) as the SQL database.
- 🚀 [React](https://react.dev) for the frontend.
  - 🧩 Built into the backend application and served by FastAPI on the same domain as the API.
  - 💃 Using TypeScript, hooks, [Vite](https://vitejs.dev), and other parts of a modern frontend stack.
  - 🎨 [Tailwind CSS](https://tailwindcss.com) and [shadcn/ui](https://ui.shadcn.com) for the frontend components.
  - 🤖 An automatically generated frontend client.
  - 🧪 [Playwright](https://playwright.dev) for end-to-end testing.
  - 🦇 Dark mode support.
- ☁️ [FastAPI Cloud](https://fastapicloud.com) for deployment.
- 🐋 [Docker Compose](https://www.docker.com) for local services and self-hosted deployment.
  - 📞 [Traefik](https://traefik.io) as a reverse proxy with automatic HTTPS.
- 🔒 Secure password hashing by default.
- 🔑 JWT (JSON Web Token) authentication.
- 📫 Email-based password recovery.
- ✉️ [React Email](https://react.email) for email templates.
- 📬 [Mailpit](https://mailpit.axllent.org) for local email testing during development.
- ✅ Tests with [Pytest](https://pytest.org).
- 🏭 CI (continuous integration) and CD (continuous deployment) based on GitHub Actions.

### Dashboard Login

![Dashboard login screenshot](img/login.png)

### Dashboard - Admin

![Admin dashboard screenshot](img/dashboard.png)

### Dashboard - Items

![Items dashboard screenshot](img/dashboard-items.png)

### Dashboard - Dark Mode

![Dark mode dashboard screenshot](img/dashboard-dark.png)

### React Email Templates

![Email templates screenshot](img/react-email.png)

### Mailpit - Local Email Testing

![Mailpit screenshot](img/mailpit.png)

### Interactive API Documentation

![API docs](img/docs.png)

## How to Use It

Click the **Use this template** button at the top of this page to create a new repository.

## Backend Development

Backend docs: [backend/README.md](./backend/README.md).

## Frontend Development

Frontend docs: [frontend/README.md](./frontend/README.md).

## Deployment

FastAPI Cloud deployment: [deployment.md](./deployment.md).

Self-hosted deployment with Docker Compose: [deployment-docker-compose.md](./deployment-docker-compose.md).

## Development

General development docs: [development.md](./development.md).

This includes the local FastAPI and Vite workflow, Docker Compose services, `.env` configuration, and more.

## Release Notes

Check the file [release-notes.md](./release-notes.md).

## License

The Full Stack FastAPI Template is licensed under the terms of the MIT license.
