"""
Lightweight ADQL-to-PostgreSQL translator using pg_sphere for geometry.

Supported transforms
──────────────────────────────────────────────────────────
  SELECT TOP n                  → SELECT … LIMIT n
  1 = CONTAINS(…) idiom         → bare boolean expression
  POINT(sys, ra, dec)           → spoint(radians(ra), radians(dec))
  CIRCLE(sys, ra, dec, r)       → scircle(center_spoint, radians(r))
  BOX(sys, ra, dec, w, h)       → sbox(sw_spoint, ne_spoint)
  POLYGON(sys, ra1,dec1, …)     → (spoint[])::spoly
  CONTAINS(region, point)       → (region @> point)
  INTERSECTS(region1, region2)  → (region1 && region2)
  DISTANCE(p1, p2)              → degrees(p1 <-> p2)

Prerequisites
──────────────────────────────────────────────────────────
  The pg_sphere PostgreSQL extension must be installed:
    python manage.py setup_pgsphere
"""

import re

_TOP_RE = re.compile(r'(?i)^\s*SELECT\s+TOP\s+(\d+)\s+')

_GEO_FUNC_RE = re.compile(
    r'\b(POINT|CIRCLE|BOX|POLYGON|CONTAINS|INTERSECTS|DISTANCE'
    r'|CENTROID|COORD1|COORD2|COORDSYS|AREA)\s*\(',
    re.IGNORECASE,
)

# The common ADQL idiom "1 = CONTAINS(...)" — pg_sphere operators return bool.
_ONE_EQ_GEO_RE = re.compile(
    r'\b1\s*=\s*(?=(?:CONTAINS|INTERSECTS)\s*\()',
    re.IGNORECASE,
)


# ── Argument parser ────────────────────────────────────────────────────────────

def _parse_args(query: str, start: int) -> tuple[list[str], int]:
    """
    Read comma-separated function arguments starting at `start` (immediately
    after the opening parenthesis).  Returns (args, index_after_closing_paren).
    Handles nested parentheses and single-quoted SQL string literals.
    """
    args: list[str] = []
    buf:  list[str] = []
    depth = 0
    i = start

    while i < len(query):
        ch = query[i]

        if ch == "'":
            # Consume the entire string literal (handle '' escape).
            buf.append(ch)
            i += 1
            while i < len(query):
                c = query[i]
                buf.append(c)
                i += 1
                if c == "'":
                    if i < len(query) and query[i] == "'":
                        buf.append(query[i])
                        i += 1
                    else:
                        break
            continue

        if ch == '(':
            depth += 1
            buf.append(ch)
        elif ch == ')':
            if depth == 0:
                stripped = ''.join(buf).strip()
                if stripped:
                    args.append(stripped)
                return args, i + 1
            depth -= 1
            buf.append(ch)
        elif ch == ',' and depth == 0:
            args.append(''.join(buf).strip())
            buf = []
        else:
            buf.append(ch)

        i += 1

    raise ValueError("Unclosed parenthesis in ADQL geometry expression")


# ── Per-function translation ───────────────────────────────────────────────────

def _geo_to_pgsphere(func: str, raw_args: list[str]) -> tuple[str, str | None]:
    """
    Recursively translate each argument, then map the ADQL function call to
    its pg_sphere / SQL equivalent.
    Returns (sql_expression, error_message).
    """
    # Translate any nested geometry inside arguments first.
    args: list[str] = []
    for raw in raw_args:
        translated, err = translate(raw)
        if err:
            return '', err
        args.append(translated)

    n = len(args)
    f = func.upper()

    if f == 'POINT':
        # POINT('coordsys', ra, dec)  →  spoint(radians(ra), radians(dec))
        if n < 3:
            return '', f"POINT() needs 3 args (coordsys, ra, dec); got {n}"
        ra, dec = args[1], args[2]
        return f'spoint(radians(({ra})::float8), radians(({dec})::float8))', None

    if f == 'CIRCLE':
        # CIRCLE('coordsys', ra, dec, radius_deg)
        if n < 4:
            return '', f"CIRCLE() needs 4 args; got {n}"
        ra, dec, r = args[1], args[2], args[3]
        center = f'spoint(radians(({ra})::float8), radians(({dec})::float8))'
        return f'scircle({center}, radians(({r})::float8))', None

    if f == 'BOX':
        # BOX('coordsys', ra, dec, width, height)  — center + half-extents
        if n < 5:
            return '', f"BOX() needs 5 args; got {n}"
        ra, dec, w, h = args[1], args[2], args[3], args[4]
        sw = (f'spoint(radians(({ra}) - ({w})/2.0)::float8, '
              f'radians(({dec}) - ({h})/2.0)::float8)')
        ne = (f'spoint(radians(({ra}) + ({w})/2.0)::float8, '
              f'radians(({dec}) + ({h})/2.0)::float8)')
        return f'sbox({sw}, {ne})', None

    if f == 'POLYGON':
        # POLYGON('coordsys', ra1, dec1, ra2, dec2, …)
        coords = args[1:]  # drop coordsys
        if len(coords) < 6 or len(coords) % 2 != 0:
            return '', "POLYGON() needs coordsys + at least 3 ra/dec pairs"
        points = ', '.join(
            f'spoint(radians(({coords[i]})::float8), radians(({coords[i+1]})::float8))'
            for i in range(0, len(coords), 2)
        )
        return f'(ARRAY[{points}]::spoint[])::spoly', None

    if f == 'CONTAINS':
        if n != 2:
            return '', f"CONTAINS() needs 2 args; got {n}"
        return f'(({args[0]}) @> ({args[1]}))', None

    if f == 'INTERSECTS':
        if n != 2:
            return '', f"INTERSECTS() needs 2 args; got {n}"
        return f'(({args[0]}) && ({args[1]}))', None

    if f == 'DISTANCE':
        if n != 2:
            return '', f"DISTANCE() needs 2 args; got {n}"
        return f'degrees(({args[0]}) <-> ({args[1]}))', None

    return '', (
        f"ADQL function {func}() is not yet supported. "
        "Supported: POINT, CIRCLE, BOX, POLYGON, CONTAINS, INTERSECTS, DISTANCE."
    )


# ── Public entry point ─────────────────────────────────────────────────────────

def translate(query: str) -> tuple[str, str | None]:
    """
    Translate an ADQL query string to PostgreSQL SQL.
    Returns (sql, error) where error is None on success.

    Steps applied in order:
      1. SELECT TOP n  →  SELECT … LIMIT n
      2. Strip "1 = CONTAINS/INTERSECTS" prefix (pg_sphere returns bool)
      3. Translate ADQL geometry functions to pg_sphere (innermost-first via recursion)
    """
    # 1. TOP n → LIMIT n (matched only at query start)
    limit: str | None = None
    m = _TOP_RE.match(query)
    if m:
        limit = m.group(1)
        query = 'SELECT ' + query[m.end():].rstrip().rstrip(';')

    # 2. "1 = CONTAINS/INTERSECTS" → just the function call (returns bool in pg_sphere)
    query = _ONE_EQ_GEO_RE.sub('', query)

    # 3. Geometry function translation (recursive, innermost-first)
    result: list[str] = []
    i = 0
    while i < len(query):
        m = _GEO_FUNC_RE.search(query, i)
        if not m:
            result.append(query[i:])
            break
        result.append(query[i:m.start()])
        func = m.group(1)
        raw_args, i = _parse_args(query, m.end())  # m.end() is after '('
        pg_expr, err = _geo_to_pgsphere(func, raw_args)
        if err:
            return query, err
        result.append(pg_expr)

    query = ''.join(result)
    if limit:
        query = query.rstrip(';') + f' LIMIT {limit}'

    return query, None
