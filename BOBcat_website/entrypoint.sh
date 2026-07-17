#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
while ! python -c "
import psycopg2, os, sys
try:
    psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB','bobcat'),
        user=os.environ.get('POSTGRES_USER','postgres'),
        password=os.environ.get('POSTGRES_PASSWORD',''),
        host=os.environ.get('POSTGRES_HOST','db'),
        port=os.environ.get('POSTGRES_PORT','5432'),
    )
except Exception:
    sys.exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
python manage.py migrate --no-input

echo "Installing pg_sphere extension..."
python manage.py setup_pgsphere || true

echo "Setting up read-only database user..."
python manage.py setup_readonly_db_user || true

# Runtime application role — non-superuser, DML only. Created here while we're
# still connected as the superuser POSTGRES_USER (migrations and
# CREATE EXTENSION above need that); the serving process below then drops to
# this role so a compromised gunicorn worker can't run DDL, read server files,
# or reach other databases. Re-run after migrate so it picks up any new tables.
export APP_DB_USER="${APP_DB_USER:-bobcat_app}"
export APP_DB_PASSWORD="${APP_DB_PASSWORD:-bobcat_app_pw}"
echo "Setting up application database user..."
python manage.py setup_app_user || true

echo "Collecting static files..."
python manage.py collectstatic --no-input

if [ "$#" -gt 0 ]; then
    # Admin/batch commands (e.g. the `ingest` service's Jordans_ingestion) keep
    # the superuser connection — they legitimately bulk-write and are not the
    # public runtime this hardening targets.
    echo "Running command: $@"
    exec "$@"
fi

# Drop the default connection from the superuser POSTGRES_USER to the
# non-superuser app role for the public-facing gunicorn process only. settings
# reads POSTGRES_USER/PASSWORD for the `default` DB; the separate `readonly`
# connection uses its own READONLY_* env and is unaffected.
export POSTGRES_USER="$APP_DB_USER"
export POSTGRES_PASSWORD="$APP_DB_PASSWORD"

echo "Starting gunicorn as non-superuser role '$APP_DB_USER'..."
exec gunicorn BOBcat_website.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers 3 \
    --timeout 120
