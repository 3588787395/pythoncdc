# r4 minimal liveness probe: single-case literal value match


def match_value_single(x):
    """Minimal match: one literal value case with default."""
    match x:
        case 1:
            return "one"
        case _:
            return "other"


def match_value_two(x):
    """Two literal value cases."""
    match x:
        case 1:
            return "one"
        case 2:
            return "two"
    return "none"
