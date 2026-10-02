# rv4 (REVIEW2 variant): B12 - or pattern containing mapping shapes + or with as-capture


def or_map_nested(d):
    """V1: or alternatives are mapping/sequence shapes (same-bound-names)."""
    match d:
        case {"a": 1} | {"a": 2}:
            return "or-map-lit"
        case {"a": v1} | {"b": [v1, _]}:
            return "or-map-cap"
        case _:
            return "no"


def or_as_capture(d):
    """V2: or of literals with as-capture; or of shapes with as-capture."""
    match d:
        case 1 | 2 as v:
            return ("num", v)
        case {"k": w1} | {"k": w1, "j": _} as w:
            return ("shape", w)
        case _:
            return "other"


def or_mixed_deep(d):
    """V3: three alternatives mixing nested mapping and starred sequence."""
    match d:
        case {"x": {"y": 1}} | {"x": {"y": 2}} | [1, 2]:
            return "deep-or"
        case _:
            return "no"
