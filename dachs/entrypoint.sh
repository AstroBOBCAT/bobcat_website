#!/bin/bash
set -e

echo "Writing /etc/gavo.rc ..."
cat > /etc/gavo.rc <<GAVORC
[general]
rootDir: /var/gavo

[web]
serverURL: ${DACHS_SERVER_URL:-http://localhost}
serverPort: 8080
bindAddress: 0.0.0.0
GAVORC

mkdir -p /var/gavo/etc /var/gavo/logs /var/gavo/inputs/bobcat

# Build the superuser DSN. POSTGRES_USER is created as SUPERUSER by the
# postgres Docker image, so gavo init can use it to create roles/schemas.
SUPERUSER_DSN="host=${POSTGRES_HOST:-db} port=${POSTGRES_PORT:-5432} dbname=${POSTGRES_DB:-bobcat} user=${POSTGRES_USER:-bobcat_user} password=${POSTGRES_PASSWORD}"

echo "Initialising DACHS schemas in PostgreSQL ..."
# gavo init -d DSN creates _gavo/tap_schema schemas and the gavoadmin/gavo/
# untrusted roles. It also writes profile files. || true so restarts are safe.
gavo init -d "$SUPERUSER_DSN" || true

echo "Writing database profiles ..."
# Override gavo init's profiles to reuse POSTGRES_USER (already a superuser
# with full table access) rather than the gavoadmin role it created.
cat > /var/gavo/etc/dsn <<PROF
host=${POSTGRES_HOST:-db}
port=${POSTGRES_PORT:-5432}
database=${POSTGRES_DB:-bobcat}
user=${POSTGRES_USER:-bobcat_user}
password=${POSTGRES_PASSWORD}
PROF

printf 'include dsn\n' > /var/gavo/etc/feed
printf 'include dsn\n' > /var/gavo/etc/trustedquery
printf 'include dsn\n' > /var/gavo/etc/untrustedquery

echo "Creating bobcat schema with views over public tables ..."
# DaCHS's ADQL grammar treats PUBLIC as a reserved word so tables registered
# under schema="public" can't be queried. We use schema="bobcat" in the RD
# and create a matching PostgreSQL schema containing views of the real tables.
psql "host=${POSTGRES_HOST:-db} port=${POSTGRES_PORT:-5432} dbname=${POSTGRES_DB:-bobcat} user=${POSTGRES_USER:-bobcat_user} password=${POSTGRES_PASSWORD}" <<'SQL'
CREATE SCHEMA IF NOT EXISTS bobcat;
CREATE OR REPLACE VIEW bobcat.candidate           AS SELECT * FROM public.candidate;
CREATE OR REPLACE VIEW bobcat.bib                 AS SELECT * FROM public.bib;
CREATE OR REPLACE VIEW bobcat.binary_model        AS SELECT * FROM public.binary_model;
CREATE OR REPLACE VIEW bobcat.obs_period          AS SELECT * FROM public.obs_period;
CREATE OR REPLACE VIEW bobcat.binary_model_error  AS SELECT * FROM public.binary_model_error;
CREATE OR REPLACE VIEW bobcat.evidence_subcategory AS SELECT * FROM public.evidence_subcategory;
CREATE OR REPLACE VIEW bobcat.model_evidence      AS SELECT * FROM public.model_evidence;
SQL

echo "Importing BOBcat resource descriptor ..."
gavo imp /var/gavo/inputs/bobcat/q.rd

echo "Publishing resource (optional; no-op for local-only deployment) ..."
gavo pub /var/gavo/inputs/bobcat/q.rd || true

echo "Starting DACHS server (foreground) ..."
exec gavo serve debug
