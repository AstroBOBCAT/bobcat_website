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

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Starting gunicorn..."
exec gunicorn BOBcat_website.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120
