# `db/` — PostgreSQL database image

Builds the `db` service in `docker-compose.yml`: the PostgreSQL instance that
holds all BOBcat catalog data.

## What's here

- **`Dockerfile`** — extends the official `postgres:15` image and installs two
  spatial extensions from the PostgreSQL apt repo the base image already
  configures:
  - **`postgresql-15-pgsphere`** — spherical geometry types/operators
    (`spoint`, `scircle`, …) that DaCHS's ADQL layer uses for cone/region
    searches.
  - **`postgresql-15-q3c`** — sky-indexing extension for fast positional
    (RA/Dec) queries.

  The extensions are only *installed* here; they're enabled inside the database
  by `manage.py setup_pgsphere` (run from the backend's `entrypoint.sh`), not by
  this Dockerfile.

## How it fits

- Data lives in the named volume `postgres_data` (see `docker-compose.yml`), so
  it survives container restarts and rebuilds. `docker compose down -v` **wipes
  it** — that's how you get a from-scratch database.
- Credentials and DB name come from the git-ignored `.db_info` env file
  (`POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, plus the read-only /
  app-role passwords).
- The service has **no published port** — it's reachable only on the
  compose-internal network by the `backend`, `dachs`, and `ingest` services.
- `POSTGRES_USER` is created by the base image as a **superuser**; the web
  runtime deliberately connects as a lower-privileged role instead (see the
  backend `entrypoint.sh` and the `setup_readonly_db_user` / `setup_app_user`
  management commands).

## Consumers

- **`backend`** (Django) — owns the schema via migrations; runs queries as the
  non-superuser app role, and user-submitted SQL as the locked-down
  `bobcat_readonly` role.
- **`dachs`** — reads the same tables through `bobcat.*` views for TAP; see
  `../dachs/README.md`.
