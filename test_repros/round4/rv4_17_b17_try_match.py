# rv4 (REVIEW2 variant): B17 - try/except/else wrapping match + case body raising into try


def try_else_match(x):
    """V1: try/except/else wrapping a match (else clause present)."""
    try:
        match x:
            case 1:
                r = "one"
            case _:
                r = "other"
    except TypeError:
        return "bad"
    else:
        return r + "!"


def case_body_raise(x):
    """V2: case body raises; exception propagates to enclosing try handler."""
    try:
        match x:
            case 1:
                raise ValueError("boom")
            case _:
                return "ok"
    except ValueError as e:
        return ("caught", str(e))
    return "unreachable"


def try_finally_match(x):
    """V3: try/finally wrapping match (finally, no except)."""
    log = []
    try:
        match x:
            case 1:
                log.append("one")
            case 2:
                log.append("two")
    finally:
        log.append("end")
    return log
