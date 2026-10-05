"""x07: except* at depth >= 3 (A7/C3 depth extrapolation)."""
def ts_shallow():
    try:
        raise ExceptionGroup('g', [ValueError('x')])
    except* ValueError as eg:
        R = eg
    return 1


def ts_in_for():
    for i in range(1):
        try:
            if i:
                try:
                    raise ExceptionGroup('g', [TypeError('t')])
                except* TypeError as eg:
                    R = eg
        finally:
            F = i
    return 2


def ts_with_fin():
    try:
        with _A():
            try:
                raise ExceptionGroup('g', [ValueError('v')])
            except* ValueError as eg:
                R = 1
    finally:
        F = 2
    return 3
