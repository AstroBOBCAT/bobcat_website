import pytest

from mainpage.adql import _geo_to_pgsphere, _parse_args, translate


# ── _parse_args ──────────────────────────────────────────────────────────────

def test_parse_args_simple():
    args, idx = _parse_args("1, 2, 3)", 0)
    assert args == ["1", "2", "3"]
    assert idx == len("1, 2, 3)")


def test_parse_args_nested_parens_stay_intact():
    args, idx = _parse_args("(a+b), 2)", 0)
    assert args == ["(a+b)", "2"]


def test_parse_args_quoted_string_with_escaped_quote_not_split_on_comma():
    args, idx = _parse_args("'J2000', 'it''s, odd', 3)", 0)
    assert args == ["'J2000'", "'it''s, odd'", "3"]


def test_parse_args_unclosed_paren_raises_valueerror():
    with pytest.raises(ValueError):
        _parse_args("1, 2", 0)


# ── translate: TOP / idiom stripping / passthrough ──────────────────────────

def test_translate_select_top_n_to_limit():
    sql, err = translate("SELECT TOP 10 * FROM binary_model")
    assert err is None
    assert sql.rstrip().endswith("LIMIT 10")
    assert "TOP" not in sql


def test_translate_one_eq_contains_idiom_stripped():
    sql, err = translate(
        "SELECT * FROM binary_model WHERE 1 = CONTAINS(a, b)"
    )
    assert err is None
    assert "1 =" not in sql
    assert "@>" in sql


def test_translate_no_geometry_passthrough():
    query = "SELECT * FROM binary_model WHERE mtot > 8"
    sql, err = translate(query)
    assert err is None
    assert sql == query


# ── POINT ────────────────────────────────────────────────────────────────────

def test_translate_point_to_spoint():
    sql, err = _geo_to_pgsphere("POINT", ["'J2000'", "10.0", "20.0"])
    assert err is None
    assert "spoint(" in sql
    assert "radians(" in sql


def test_translate_point_needs_3_args_errors():
    sql, err = _geo_to_pgsphere("POINT", ["'J2000'", "10.0"])
    assert sql == ""
    assert err is not None
    assert "3 args" in err


# ── CIRCLE ───────────────────────────────────────────────────────────────────

def test_translate_circle_to_scircle():
    sql, err = _geo_to_pgsphere("CIRCLE", ["'J2000'", "10.0", "20.0", "1.0"])
    assert err is None
    assert "scircle(" in sql
    assert "radians(" in sql


def test_translate_circle_needs_4_args_errors():
    sql, err = _geo_to_pgsphere("CIRCLE", ["'J2000'", "10.0", "20.0"])
    assert sql == ""
    assert err is not None
    assert "4 args" in err


# ── BOX ──────────────────────────────────────────────────────────────────────

def test_translate_box_5_args_to_sbox():
    sql, err = _geo_to_pgsphere(
        "BOX", ["'J2000'", "10.0", "20.0", "2.0", "3.0"]
    )
    assert err is None
    assert "sbox(" in sql
    assert "/2.0" in sql


def test_translate_box_needs_5_args_errors():
    sql, err = _geo_to_pgsphere("BOX", ["'J2000'", "10.0", "20.0", "2.0"])
    assert sql == ""
    assert err is not None
    assert "5 args" in err


# ── POLYGON ──────────────────────────────────────────────────────────────────

def test_translate_polygon_valid_builds_spoly_array():
    sql, err = _geo_to_pgsphere(
        "POLYGON",
        ["'J2000'", "1", "1", "2", "2", "3", "3"],
    )
    assert err is None
    assert "ARRAY[" in sql
    assert "::spoly" in sql


def test_translate_polygon_odd_coord_count_errors():
    # coordsys + 5 raw coords (odd) -> not a valid set of ra/dec pairs
    sql, err = _geo_to_pgsphere(
        "POLYGON", ["'J2000'", "1", "1", "2", "2", "3"]
    )
    assert sql == ""
    assert err is not None
    assert "POLYGON" in err


def test_translate_polygon_too_few_pairs_errors():
    # only 1 pair after coordsys (< 3 pairs required)
    sql, err = _geo_to_pgsphere("POLYGON", ["'J2000'", "1", "1"])
    assert sql == ""
    assert err is not None
    assert "POLYGON" in err


# ── CONTAINS / INTERSECTS / DISTANCE ────────────────────────────────────────

def test_translate_contains_to_at_operator():
    sql, err = _geo_to_pgsphere("CONTAINS", ["region", "point"])
    assert err is None
    assert "@>" in sql


def test_translate_contains_wrong_arity_errors():
    sql, err = _geo_to_pgsphere("CONTAINS", ["only_one"])
    assert sql == ""
    assert err is not None
    assert "2 args" in err


def test_translate_intersects_to_double_ampersand():
    sql, err = _geo_to_pgsphere("INTERSECTS", ["region1", "region2"])
    assert err is None
    assert "&&" in sql


def test_translate_intersects_wrong_arity_errors():
    sql, err = _geo_to_pgsphere("INTERSECTS", ["a", "b", "c"])
    assert sql == ""
    assert err is not None
    assert "2 args" in err


def test_translate_distance_to_pgsphere_operator():
    sql, err = _geo_to_pgsphere("DISTANCE", ["p1", "p2"])
    assert err is None
    assert "<->" in sql
    assert "degrees(" in sql


# ── Unsupported function ────────────────────────────────────────────────────

def test_translate_unsupported_function_area_returns_error():
    sql, err = _geo_to_pgsphere("AREA", ["region"])
    assert sql == ""
    assert err is not None
    assert "not yet supported" in err


# ── Nested geometry (innermost-first) ───────────────────────────────────────

def test_translate_nested_geometry_functions_innermost_first():
    query = (
        "SELECT * FROM t WHERE "
        "CONTAINS(CIRCLE('J2000', 10, 20, 1), POINT('J2000', 11, 21)) = 1"
    )
    sql, err = translate(query)
    assert err is None
    assert "@>" in sql
    assert "scircle(" in sql
    assert "spoint(" in sql
    # No leftover ADQL function names
    assert "CIRCLE(" not in sql
    assert "POINT(" not in sql
    assert "CONTAINS(" not in sql
