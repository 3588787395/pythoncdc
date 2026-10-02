# Source Generated with Decompyle++ (Python version)
# File: rv4_17_b17_try_match.pyc (Python 3.11)

def try_else_match(x):
    """V1: try/except/else wrapping a match (else clause present)."""
    try:
        match x:
            case 1:
                r = 'one'
            case _:
                r = 'other'
    except TypeError:
        return 'bad'
def case_body_raise(x):
    """V2: case body raises; exception propagates to enclosing try handler."""
    try:
        if x == 1:
            raise ValueError('boom')
        return 'ok'
    except ValueError as e:
        return ('caught', str(e))
def try_finally_match(x):
    """V3: try/finally wrapping match (finally, no except)."""
    log = []
    try:
        match x:
            case 1:
                pass
            case 2:
                log.append('two')
    finally:
        log.append('end')
    return log
