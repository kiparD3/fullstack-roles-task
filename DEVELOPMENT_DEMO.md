# Temporary RBAC development demo

This commit intentionally includes the complete temporary development setup. The next cleanup commit removes it. Use only on your local machine with disposable data; the supplied passwords and signing key are public development defaults.

Prerequisites: Docker Compose, uv, Bun and Python 3.14. From the repository root:

```bash
uv sync --frozen --package app
bun install --frozen-lockfile
docker compose -p fullstack-roles -f compose.rbac.yml up -d --wait
source scripts/rbac-env.sh
cd backend
uv run alembic upgrade head
uv run python -m app.initial_data
uv run python -m app.seed_rbac_users
uv run uvicorn app.main:app --host 127.0.0.1 --port 18000
```

In another terminal, from the repository root:

```bash
source scripts/rbac-env.sh
cd frontend
bun run dev --host 127.0.0.1 --port 5173
```

Open http://localhost:5173 (API docs: http://localhost:18000/docs; Mailpit: http://localhost:18025).

The seed creates these accounts, skipping existing accounts without changing passwords or privileges:

- `rbac-admin@example.com`: superuser administrator.
- `rbac-manager@example.com`: manager with read-only user-list and metrics access.
- `rbac-member@example.com`: member.
- `rbac-legacy@example.com`: null role, treated as member.

The seed password comes from `RBAC_DEMO_PASSWORD`. The environment helper defaults it to `Local-demo-password-123!`. The bootstrap admin is `rbac-root@example.com` with `FIRST_SUPERUSER_PASSWORD` (same disposable default). Override passwords before sourcing if desired. The Compose PostgreSQL password must match `DATABASE_URL` if changed. The seed refuses non-development environments and never runs automatically in application startup or migrations.

## Automated tests

Create the separate backend test database once, from the root:

```bash
docker compose -p fullstack-roles -f compose.rbac.yml exec -T db createdb -U postgres rbac_test
source scripts/rbac-env.sh
cd backend
DATABASE_URL=postgresql://postgres:rbac-local-only@localhost:55432/rbac_test uv run alembic upgrade head
DATABASE_URL=postgresql://postgres:rbac-local-only@localhost:55432/rbac_test uv run pytest -q
```

Never run backend tests against the demo database: the inherited fixture deletes all users/items. With the app servers running, use another terminal from the root:

```bash
source scripts/rbac-env.sh
cd frontend
bun x playwright install chromium
bun x playwright test --workers=2
```

## Remove temporary data

Stop the frontend and backend with Ctrl+C. From the root, the following command deletes the disposable demo/test databases and all their users, plus the services:

```bash
docker compose -p fullstack-roles -f compose.rbac.yml down --volumes
```

This is a local database operation. Checking out the next cleanup commit removes the files but cannot delete an already-running database. Run this teardown first if you used the development commit. Permanent tests and the original template's local tooling remain after cleanup.
