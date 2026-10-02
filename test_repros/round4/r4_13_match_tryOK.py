# Source Generated with Decompyle++ (Python version)
# File: r4_13_match_try.pyc (Python 3.11)

def try_wrap_match(x):
    """Attack 1: try/except containing a match."""
    try:
        match x:
            case 1:
                return 'one'
            case 2:
                return 'two'
            case _:
                return 'other'
    except TypeError:
        return 'bad-type'
def try_wrap_match_body_raise(x):
    """Attack 2: try wraps match whose case body raises."""
    try:
        match x:
            case 'ok':
                return 'fine'
            case 'bad':
                raise ValueError('bad value')
            case _:
                return 'unknown'
    except ValueError as e:
        return ('caught', str(e))
def match_wrap_try(x):
    """Attack 3: match case body containing try/except."""
    match x:
        case 'risky':
            try:
                return 10 / x.__len__()
            except ZeroDivisionError:
                return 'div0'
        case 'safe':
            return 1
        case _:
            return 0
def match_wrap_try_finally(seq):
    """Attack 4: match body with try/finally."""
    log = []
    match seq:
        case [a, b]:
            try:
                log.append(a)
                log.append(b)
            finally:
                log.append('done')
        case _:
            log.append('skip')
    return log
def try_wrap_match_in_loop(items):
    """Attack 5: try/except wraps loop of matches."""
    out = []
    try:
        for item in items:
            match item:
                case n if n > 100:
                    raise RuntimeError('too big')
                case n:
                    out.append(n)
    except RuntimeError:
        out.append('aborted')
    return out
def match_case_try_loop(x):
    """Attack 6: match -> case body -> try -> loop."""
    result = []
    n = x
    try:
        for i in range(n):
            if i == 3:
                break
            result.append(i)
    except Exception:
        result.append('err')
    return result
