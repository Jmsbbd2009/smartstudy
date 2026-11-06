#!/bin/sh
set -eu
alembic upgrade head
if [ -n "${BOOTSTRAP_SUPERADMIN_LOGIN:-}" ] && [ -n "${BOOTSTRAP_SUPERADMIN_PASSWORD:-}" ]; then
  python -m app.bootstrap
fi
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-proxy-headers
