# Source from the repository root for the isolated local RBAC demo.
# These credentials are for local disposable development only.
export FASTAPI_ENV=development
export DATABASE_URL="${DATABASE_URL:-postgresql://postgres:rbac-local-only@localhost:55432/app}"
export SECRET_KEY="${SECRET_KEY:-rbac-local-development-secret-not-for-production}"
export FIRST_SUPERUSER="${FIRST_SUPERUSER:-rbac-root@example.com}"
export FIRST_SUPERUSER_PASSWORD="${FIRST_SUPERUSER_PASSWORD:-Local-demo-password-123!}"
export RBAC_DEMO_PASSWORD="${RBAC_DEMO_PASSWORD:-Local-demo-password-123!}"
export PROJECT_NAME="Fullstack Roles Task"
export FRONTEND_HOST=http://localhost:5173
export SMTP_HOST=localhost
export SMTP_PORT=11025
export SMTP_TLS=false
export EMAILS_FROM_EMAIL=noreply@example.com
export VITE_API_URL=http://localhost:18000
export MAILPIT_HOST=http://localhost:18025
