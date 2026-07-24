# `tests/` — test suite

Automated tests for the BOBcat project. Split into **unit** tests (fast, no
external services) and **integration** tests (require the live docker-compose
stack and/or external astronomy services).

Configuration lives in `../pyproject.toml` under `[tool.pytest.ini_options]`:
`testpaths = ["tests"]`, `pythonpath = ["BOBcat_website"]`,
`DJANGO_SETTINGS_MODULE = "BOBcat_website.settings"`, and a dummy
`DJANGO_SECRET_KEY` injected via `pytest-env`.

## Running

Run from the **repository root** (not from `BOBcat_website/` — pytest's config
and `testpaths` are anchored at the root):

```bash
python3 -m pytest          # unit tests only (default: -m 'not network')
python3 -m pytest -m network   # integration tests (needs the stack up)
```

The default `addopts = "-m 'not network'"` means a bare `pytest` runs only the
unit tests. The `network` marker opts in to tests that hit a live stack or
external services.

## `unit/` — fast, isolated

No network, no database connection.

- **`test_calc.py`** — `BOBcat_utils/calc.py` mass/orbit math (masses handled as
  log10 M☉; verified against the module's own equations).
- **`test_calc_sympy.py`** — the sympy-based `calc_sympy.py` drop-in; same
  numeric expectations as `test_calc.py`, plus its `CalcError` behavior.
- **`test_adql.py`** — `mainpage/adql.py`: ADQL→pg_sphere geometry translation
  and argument parsing.
- **`test_ingest_pure.py`** — the network/DB-free helpers in
  `BOBcat_utils/ingest.py` (URL building, sheet-key extraction, cell parsing).
  Importing pulls in Django, hence the dummy secret key from pytest config.
- **`*.xlsx`** — spreadsheet fixtures modeling the ingestion input format
  (the `:Zone.Identifier` files are harmless Windows download-provenance
  metadata).

## `integration/` — live stack required (`@pytest.mark.network`)

Bring the stack up first (`docker compose up`). Base URL defaults to
`http://localhost`; override with `BOBCAT_BASE_URL`.

- **`test_live_endpoints.py`** — HTTP smoke tests through nginx: Django pages on
  `/` and the TAP metadata endpoints (`/tap/availability`, `/tap/capabilities`,
  `/tap/tables`).
- **`test_tap_protocol.py`** — deeper TAP-protocol tests via **pyvo** (VOSI,
  sync/async ADQL, UWS job lifecycle). Passing means the endpoint is usable by
  real VO clients (TOPCAT, astroquery, pyvo). Skipped automatically if `pyvo`
  isn't installed.

## Notes

- Integration tests run on the **host**, not inside the containers (the runtime
  image doesn't ship pytest/pyvo — install those in your host environment).
- Unit tests never touch the dev Postgres database; ingestion-related tests use
  in-memory / fixture data.
