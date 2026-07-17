"""TAP-protocol tests against the running DaCHS service, via pyvo.

Requires the stack to actually be up (`docker compose up`) — opt in with
`-m network`, same convention as tests/integration/test_live_endpoints.py.
Base URL defaults to http://localhost; override with BOBCAT_BASE_URL for
other envs.

These go beyond the bare-HTTP smoke tests: pyvo speaks the IVOA Table Access
Protocol (VOSI availability/capabilities/tables, sync and async ADQL, UWS job
lifecycle), so passing here means the TAP endpoint is usable by standard VO
clients (TOPCAT, astroquery, pyvo).
"""
import os
import time
import warnings

import pytest

pyvo = pytest.importorskip("pyvo")

from astropy.table import Table  # noqa: E402
from pyvo.dal import DALQueryError, TAPService  # noqa: E402

BASE_URL = os.environ.get("BOBCAT_BASE_URL", "http://localhost").rstrip("/")
TAP_URL = f"{BASE_URL}/tap"

# Hard ceiling on the async (UWS) job test so a stuck job can't hang the run.
ASYNC_DEADLINE = 60  # seconds
POLL_INTERVAL = 2  # seconds

# Views exposed by dachs/inputs/bobcat/q.rd.
EXPECTED_TABLES = [
    "bobcat.candidate",
    "bobcat.bib",
    "bobcat.binary_model",
    "bobcat.obs_period",
    "bobcat.binary_model_error",
    "bobcat.evidence_subcategory",
    "bobcat.model_evidence",
]

SYNC_QUERY = "SELECT TOP 5 * FROM bobcat.candidate"

# DaCHS's metadata documents are standards-compliant but trip pedantic
# astropy/pyvo VO warnings on some versions; those are noise here.
warnings.filterwarnings("ignore", category=Warning, module=r"pyvo\..*")
warnings.filterwarnings("ignore", category=Warning, module=r"astropy\.io\.votable\..*")


@pytest.fixture(scope="module")
def tap_service():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return TAPService(TAP_URL)


# ── VOSI metadata endpoints ──────────────────────────────────────────────────

@pytest.mark.network
def test_vosi_availability_reports_available(tap_service):
    assert tap_service.available, "VOSI /tap/availability reports unavailable"


@pytest.mark.network
def test_vosi_capabilities_include_tap(tap_service):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        capabilities = tap_service.capabilities
    assert capabilities, "VOSI /tap/capabilities returned no capabilities"
    standard_ids = {
        cap.standardid.lower()
        for cap in capabilities
        if getattr(cap, "standardid", None)
    }
    assert any(sid.startswith("ivo://ivoa.net/std/tap") for sid in standard_ids), (
        f"TAP capability (ivo://ivoa.net/std/TAP) not advertised; got {standard_ids}"
    )


@pytest.mark.network
def test_tables_metadata_lists_bobcat_views(tap_service):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        table_names = {name.lower() for name in tap_service.tables.keys()}
    missing = [t for t in EXPECTED_TABLES if t not in table_names]
    assert not missing, f"tables endpoint missing {missing}; got {sorted(table_names)}"


@pytest.mark.network
def test_candidate_table_has_expected_columns(tap_service):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        candidate = tap_service.tables["bobcat.candidate"]
    column_names = {col.name.lower() for col in candidate.columns}
    for expected in ("name", "jra", "jdec"):
        assert expected in column_names, (
            f"bobcat.candidate missing column {expected!r}; got {sorted(column_names)}"
        )


# ── synchronous ADQL ─────────────────────────────────────────────────────────

@pytest.mark.network
def test_sync_adql_query_returns_astropy_table(tap_service):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = tap_service.search(SYNC_QUERY)
        table = result.to_table()
    assert isinstance(table, Table)
    # Row count may legitimately be 0 on an empty DB — assert on structure only.
    for expected in ("name", "jra", "jdec"):
        assert expected in {c.lower() for c in table.colnames}, (
            f"sync result missing column {expected!r}; got {table.colnames}"
        )


# ── asynchronous ADQL (UWS job lifecycle) ────────────────────────────────────

@pytest.mark.network
def test_async_adql_job_lifecycle(tap_service):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        job = tap_service.submit_job(SYNC_QUERY)
    try:
        assert job.phase in ("PENDING", "QUEUED", "EXECUTING", "COMPLETED"), (
            f"unexpected phase after submit: {job.phase}"
        )
        job.run()

        deadline = time.monotonic() + ASYNC_DEADLINE
        while job.phase not in ("COMPLETED", "ERROR", "ABORTED"):
            assert time.monotonic() < deadline, (
                f"async job did not finish within {ASYNC_DEADLINE}s; "
                f"stuck in phase {job.phase}"
            )
            time.sleep(POLL_INTERVAL)

        assert job.phase == "COMPLETED", (
            f"async job ended in phase {job.phase}"
        )
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            table = job.fetch_result().to_table()
        assert isinstance(table, Table)
        assert "name" in {c.lower() for c in table.colnames}, (
            f"async result missing 'name' column; got {table.colnames}"
        )
    finally:
        try:
            job.delete()
        except Exception:
            pass  # best-effort cleanup; don't mask the real failure


# ── error behaviour ──────────────────────────────────────────────────────────

@pytest.mark.network
def test_malformed_adql_raises_dal_query_error(tap_service):
    with pytest.raises(DALQueryError):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tap_service.search("SELECT FROM WHERE this is not ADQL")
