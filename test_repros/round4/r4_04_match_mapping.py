# r4_04 attack: mapping patterns ({"k": v, **rest})


def match_map_basic(d):
    """Attack 1: basic mapping pattern with two keys."""
    match d:
        case {"name": n, "age": a}:
            return (n, a)
        case _:
            return None


def match_map_rest(d):
    """Attack 2: mapping with **rest capture."""
    match d:
        case {"type": t, **rest}:
            return (t, sorted(rest.keys()))
        case _:
            return "nomap"


def match_map_nested(d):
    """Attack 3: nested mapping pattern."""
    match d:
        case {"user": {"name": n, "roles": [r, *others]}}:
            return (n, r, len(others))
        case {"user": {"name": n}}:
            return (n, "noroles", 0)
        case _:
            return "nokey"


def match_map_literal_values(d):
    """Attack 4: mapping with literal value constraints."""
    match d:
        case {"status": "ok", "code": 200}:
            return "ok200"
        case {"status": "err"}:
            return "err"
        case {"status": s}:
            return ("status", s)
        case _:
            return "nostatus"


def match_map_mixed_seq(d):
    """Attack 5: mapping + sequence hybrid pattern."""
    match d:
        case {"points": [(x1, y1), (x2, y2)]}:
            return ((x1, y1), (x2, y2))
        case {"points": []}:
            return ()
        case _:
            return "nopoints"
