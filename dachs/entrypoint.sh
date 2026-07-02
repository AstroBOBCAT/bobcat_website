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

echo "Granting DACHS service roles access to DaCHS's internal 'dc' schema ..."
# gavo init (re)creates the dc schema on every run but only ever grants
# bobcat_user explicit USAGE/CREATE on it. That's not enough: Postgres's
# foreign-key CASCADE trigger machinery additionally requires the
# *referenced table's owner* (gavoadmin, which owns dc.tablemeta and its
# dependents) to hold an *explicit* schema-USAGE grant -- owning the schema
# itself isn't sufficient for this specific internal check, and superuser
# status on the connecting role doesn't bypass it either (see
# https://www.postgresql.org/message-id/20170406020941.25934.30410@wrigleys.postgresql.org).
# Without this, `gavo imp`'s metadata refresh fails with "permission denied
# for schema dc" while cascading a DELETE from dc.tablemeta to
# dc.simple_col_stats / dc.discrete_string_values, and the container
# crash-loops. Re-run on every start since gavo init resets this each time.
psql "host=${POSTGRES_HOST:-db} port=${POSTGRES_PORT:-5432} dbname=${POSTGRES_DB:-bobcat} user=${POSTGRES_USER:-bobcat_user} password=${POSTGRES_PASSWORD}" <<'SQL'
GRANT USAGE, CREATE ON SCHEMA dc TO gavoadmin, gavo, untrusted;

-- Every other object gavo init manages in dc.* is owned by gavoadmin (the
-- schema owner); if any of them ever end up owned by someone else instead
-- (e.g. bobcat_user, from a connection that bypassed the normal profile
-- setup), gavo init's own "(//services)" RD import fails non-fatally with
-- "must be owner of view <name>" when it tries CREATE OR REPLACE VIEW as
-- gavoadmin -- ownership can't be fixed by GRANT, only by ALTER ... OWNER.
DO $$
DECLARE
  rec record;
BEGIN
  FOR rec IN
    SELECT relname, relkind FROM pg_class
    WHERE relnamespace = 'dc'::regnamespace
      AND relowner != 'gavoadmin'::regrole
      AND relkind IN ('r', 'v')
  LOOP
    IF rec.relkind = 'v' THEN
      EXECUTE format('ALTER VIEW dc.%I OWNER TO gavoadmin', rec.relname);
    ELSE
      EXECUTE format('ALTER TABLE dc.%I OWNER TO gavoadmin', rec.relname);
    END IF;
  END LOOP;
END $$;
SQL

echo "Creating bobcat schema (placeholder tables for gavo imp) ..."
# q.rd declares these tables onDisk="True" adql="True", which DaCHS treats
# as tables IT manages: gavo imp (re)creates them as empty plain tables if
# they don't already match its expected DDL. So the schema needs to exist,
# but whatever we put in bobcat.* here will be overwritten by gavo imp --
# the real (idempotent) view creation happens after gavo imp/pub, below.
psql "host=${POSTGRES_HOST:-db} port=${POSTGRES_PORT:-5432} dbname=${POSTGRES_DB:-bobcat} user=${POSTGRES_USER:-bobcat_user} password=${POSTGRES_PASSWORD}" <<'SQL'
CREATE SCHEMA IF NOT EXISTS bobcat;
SQL

echo "Importing BOBcat resource descriptor ..."
gavo imp /var/gavo/inputs/bobcat/q.rd

echo "Publishing resource (optional; no-op for local-only deployment) ..."
gavo pub /var/gavo/inputs/bobcat/q.rd || true

echo "Replacing bobcat schema tables with views over public tables ..."
# DaCHS's ADQL grammar treats PUBLIC as a reserved word so tables registered
# under schema="public" can't be queried. We use schema="bobcat" in the RD
# and create a matching PostgreSQL schema containing views of the real
# tables. This must run AFTER gavo imp/gavo pub above: DaCHS recreates
# bobcat.* as its own empty managed tables during import (see comment
# above), which would otherwise clobber a view created any earlier.
psql "host=${POSTGRES_HOST:-db} port=${POSTGRES_PORT:-5432} dbname=${POSTGRES_DB:-bobcat} user=${POSTGRES_USER:-bobcat_user} password=${POSTGRES_PASSWORD}" <<'SQL'
-- gavo imp leaves these as plain tables, which makes CREATE OR REPLACE VIEW
-- below fail with "... is not a view". Drop them first so view creation is
-- idempotent no matter what object type currently occupies the name.
DO $$
DECLARE
  tbl text;
BEGIN
  FOREACH tbl IN ARRAY ARRAY['candidate','bib','binary_model','obs_period',
      'binary_model_error','evidence_subcategory','model_evidence']
  LOOP
    IF EXISTS (
      SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
      WHERE n.nspname = 'bobcat' AND c.relname = tbl AND c.relkind = 'r'
    ) THEN
      EXECUTE format('DROP TABLE bobcat.%I CASCADE', tbl);
    END IF;
  END LOOP;
END $$;

CREATE OR REPLACE VIEW bobcat.candidate           AS SELECT * FROM public.candidate;
CREATE OR REPLACE VIEW bobcat.bib                 AS SELECT * FROM public.bib;
CREATE OR REPLACE VIEW bobcat.binary_model        AS SELECT * FROM public.binary_model;
CREATE OR REPLACE VIEW bobcat.obs_period          AS SELECT * FROM public.obs_period;
CREATE OR REPLACE VIEW bobcat.binary_model_error  AS SELECT * FROM public.binary_model_error;
CREATE OR REPLACE VIEW bobcat.evidence_subcategory AS SELECT * FROM public.evidence_subcategory;
CREATE OR REPLACE VIEW bobcat.model_evidence      AS SELECT * FROM public.model_evidence;

-- Same gap as schema dc: only bobcat_user had USAGE on this schema, so
-- DaCHS's query-execution roles (gavo = trusted ADQL, untrusted = anonymous
-- TAP queries) got "permission denied for schema bobcat" on every actual
-- data query, even though the metadata endpoints (/tap/tables etc.) worked
-- fine. Views run with the owner's (bobcat_user, superuser) privileges
-- against the underlying public.* tables, so granting SELECT on the views
-- here is sufficient -- no grants on public.* itself are needed.
GRANT USAGE ON SCHEMA bobcat TO gavo, untrusted;
GRANT SELECT ON
  bobcat.candidate, bobcat.bib, bobcat.binary_model, bobcat.obs_period,
  bobcat.binary_model_error, bobcat.evidence_subcategory, bobcat.model_evidence
  TO gavo, untrusted;
SQL

echo "Starting DACHS server (foreground) ..."
exec gavo serve debug
