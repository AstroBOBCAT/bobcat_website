"""
Tests for the network/DB-free helper functions in BOBcat_utils/ingest.py.

Importing this module pulls in Django (ingest.py does
`from mainpage.models import ...`), which is why tests/conftest.py sets a
dummy DJANGO_SECRET_KEY before collection -- but none of the functions
tested here open a database connection or make network calls.
"""
import pandas as pd
import pytest

from BOBcat_utils.ingest import (
    _csv_url,
    _extract_sheet_key,
    _get_cell,
    _index_param_sheet,
    _is_blank,
    _safe_float,
    extract_bibcode,
)


# ── _csv_url ─────────────────────────────────────────────────────────────────

def test_csv_url_builds_expected_url():
    assert _csv_url("abc") == (
        "https://docs.google.com/spreadsheet/ccc?key=abc&output=csv"
    )


def test_csv_url_rejects_non_string():
    with pytest.raises(TypeError) as excinfo:
        _csv_url(3)
    assert str(excinfo.value) == "Sheet key must be a string"


# ── _extract_sheet_key ───────────────────────────────────────────────────────

def test_extract_sheet_key_from_url():
    url = "https://docs.google.com/spreadsheets/d/KEY123/edit#gid=0"
    assert _extract_sheet_key(url) == "KEY123"


# ── extract_bibcode ──────────────────────────────────────────────────────────

def test_extract_bibcode_adsabs_url():
    link = "https://ui.adsabs.harvard.edu/abs/2020ApJ...900..102A/abstract"
    scix_link, bibcode = extract_bibcode(link)
    assert bibcode == "2020ApJ...900..102A"
    assert scix_link == "https://scixplorer.org/abs/2020ApJ...900..102A"


def test_extract_bibcode_scixplorer_url():
    link = "https://scixplorer.org/abs/2020ApJ...900..102A/abstract"
    scix_link, bibcode = extract_bibcode(link)
    assert bibcode == "2020ApJ...900..102A"


def test_extract_bibcode_ampersand_escape():
    link = "https://ui.adsabs.harvard.edu/abs/2001A%26A...373..381B/abstract"
    _, bibcode = extract_bibcode(link)
    assert bibcode == "2001A&A...373..381B"


def test_extract_bibcode_unrecognized_domain_returns_link_and_empty():
    link = "https://example.com/not-an-ads-link"
    scix_link, bibcode = extract_bibcode(link)
    assert scix_link == link
    assert bibcode == ""


# ── _safe_float ──────────────────────────────────────────────────────────────

def test_safe_float_parses_numeric_string():
    assert _safe_float("3.14") == 3.14


def test_safe_float_none_returns_none():
    assert _safe_float(None) is None


@pytest.mark.parametrize(
    "val", ["", "nan", "NaN", "--", "na", "NA", "n/a", "N/A"]
)
def test_safe_float_blank_variants_return_none(val):
    assert _safe_float(val) is None


def test_safe_float_actual_nan_float_returns_none():
    assert _safe_float(float("nan")) is None


def test_safe_float_non_numeric_string_returns_none():
    assert _safe_float("not-a-number") is None


# ── _is_blank ────────────────────────────────────────────────────────────────

def test_is_blank_none():
    assert _is_blank(None) is True


@pytest.mark.parametrize("val", ["", "nan", "--", "na", "n/a", "  NA  "])
def test_is_blank_variants(val):
    assert _is_blank(val) is True


def test_is_blank_false_for_real_value():
    assert _is_blank("3.14") is False


# ── _index_param_sheet / _get_cell ──────────────────────────────────────────

def test_index_param_sheet_trims_at_first_nan_name():
    df = pd.DataFrame(
        {
            "Name": ["log(m1)", "log(m2)", None, "template row"],
            "Value": ["8.5", "8.0", None, "x"],
            "Error": [None, None, None, None],
            "Error type": [None, None, None, None],
        }
    )
    indexed = _index_param_sheet(df)
    assert list(indexed.index) == ["log(m1)", "log(m2)"]


def test_index_param_sheet_no_nan_keeps_all_rows():
    df = pd.DataFrame({"Name": ["log(m1)", "log(m2)"], "Value": ["8.5", "8.0"]})
    indexed = _index_param_sheet(df)
    assert list(indexed.index) == ["log(m1)", "log(m2)"]


def test_get_cell_returns_value_for_known_name():
    df = pd.DataFrame({"Name": ["log(m1)"], "Value": ["8.5"]}).set_index("Name")
    assert _get_cell(df, "log(m1)") == "8.5"


def test_get_cell_missing_name_returns_none():
    df = pd.DataFrame({"Name": ["log(m1)"], "Value": ["8.5"]}).set_index("Name")
    assert _get_cell(df, "log(m2)") is None


def test_get_cell_duplicate_name_rows_returns_first():
    df = pd.DataFrame(
        {"Name": ["q", "q"], "Value": ["0.5", "0.9"]}
    ).set_index("Name")
    assert _get_cell(df, "q") == "0.5"
