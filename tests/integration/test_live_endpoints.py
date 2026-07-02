"""Smoke tests against a running docker-compose stack (nginx + backend + dachs).

Requires the stack to actually be up (`docker compose up`) — opt in with
`-m network`, same convention as the NED/SIMBAD live tests in
tests/unit/test_bobcat_utils.py. Base URL defaults to the DACHS_SERVER_URL
default of http://localhost; override with BOBCAT_BASE_URL for other envs.
"""
import os

import pytest
import requests

BASE_URL = os.environ.get("BOBCAT_BASE_URL", "http://localhost").rstrip("/")
TIMEOUT = 10

# Django pages routed by nginx to the backend service (see nginx/nginx.conf).
PAGES = [
    "/",  # binary-model-search (only route currently registered in urls.py)
]

# TAP metadata endpoints routed by nginx to the dachs service. These are the
# IVOA TAP endpoints that respond to a bare GET with no query params — /tap/sync
# and /tap/async are deliberately excluded since they require a submitted ADQL
# query and legitimately 400 without one.
TAP_ENDPOINTS = [
    "/tap/availability",
    "/tap/capabilities",
    "/tap/tables",
]


# ── pages (nginx → backend) ──────────────────────────────────────────────────

@pytest.mark.network
@pytest.mark.parametrize("path", PAGES)
def test_page_returns_no_error_code(path):
    response = requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
    assert response.status_code < 400, (
        f"{path} returned {response.status_code}: {response.text[:500]}"
    )


# ── TAP endpoints (nginx → dachs) ────────────────────────────────────────────

@pytest.mark.network
@pytest.mark.parametrize("path", TAP_ENDPOINTS)
def test_tap_endpoint_returns_no_error_code(path):
    response = requests.get(f"{BASE_URL}{path}", timeout=TIMEOUT)
    assert response.status_code < 400, (
        f"{path} returned {response.status_code}: {response.text[:500]}"
    )
