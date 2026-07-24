# `dachs/` — DaCHS / IVOA TAP server image

Builds the `dachs` service in `docker-compose.yml`: a
[GAVO DaCHS](https://dachs-doc.readthedocs.io/) server that exposes the BOBcat
catalog over the **IVOA Table Access Protocol (TAP)**, so standard Virtual
Observatory clients (TOPCAT, astroquery, pyvo) can run ADQL queries against the
same data the website serves.

## What's here

- **`Dockerfile`** — Debian slim + `python3-gavo` installed from GAVO's own
  Debian repo (DaCHS isn't on PyPI). Sets `GAVO_ROOT=/var/gavo`, creates the
  `gavo` system user/group DaCHS expects, copies in `inputs/`, and runs
  `entrypoint.sh`. Exposes port **8080** (reached only via nginx `/tap`).

- **`entrypoint.sh`** — the startup logic. On boot it:
  1. Writes `/etc/gavo.rc` and DaCHS's DB **profiles**, split by privilege:
     - `feed` / `trustedquery` → the Postgres **superuser** (`gavo imp`/`gavo
       pub`, which create/manage tables and DaCHS `dc.*` metadata).
     - `untrustedquery` → a dedicated **non-superuser** role
       (`DACHS_QUERY_USER`, default `dachs_query`) that serves anonymous,
       publicly reachable TAP queries with SELECT-only rights.
  2. Runs `gavo init` once per container (guarded by a marker file so plain
     restarts don't re-run it and spam pg_sphere "already exists" noise).
  3. Creates the read-only query role and grants the DaCHS service roles
     (`gavoadmin`, `gavo`, `untrusted`) the schema access they need (there are
     long inline comments explaining several non-obvious Postgres
     ownership/grant requirements — read them before editing).
  4. Imports/publishes the resource descriptor, then replaces the imported
     `bobcat.*` tables with **views over the real `public.*` tables**.
  5. `exec gavo serve` in the foreground.

- **`inputs/bobcat/q.rd`** — the DaCHS **Resource Descriptor**: an XML mapping
  that declares each catalog table (columns, UCDs, units, types) for TAP.
  Tables are `onDisk="True"` — DaCHS reads them, it doesn't own them.

## Key design points

- **Why views, not the real tables:** DaCHS's ADQL grammar treats `PUBLIC` as a
  reserved word, so tables in Postgres's `public` schema can't be queried
  directly. The RD uses `schema="bobcat"`, and `entrypoint.sh` creates a
  `bobcat` schema of views over `public.*`. The views run with their
  superuser owner's rights, so granting `SELECT` on the views is enough — no
  grants on `public.*` are needed.
- **`/var/gavo` is not a mounted volume**, so a rebuild/recreate re-runs
  `gavo init` from scratch (intended); a plain restart skips it.
- **After a Django schema change**, re-run `gavo imp`/`gavo pub` (they run
  automatically on container recreate) so the RD and views match the new
  columns.

## Related

- Routed to the outside world by `../nginx/nginx.conf` (`/tap`, `/__system__`).
- Exercised by the TAP integration tests in `../tests/integration/`.
