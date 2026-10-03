# Source Generated with Decompyle++ (Python version)
# File: r6_11_with_trymix.pyc (Python 3.11)

def w_try_in_with(mgr):
    with mgr:
        try:
            return 1
        except ValueError:
            return 2
def w_with_in_except(mgr):
    try:
        raise ValueError(1)
    except ValueError:
        with mgr:
            return 3
def w_with_in_finally(mgr, v):
    try:
        return v
    finally:
        with mgr:
            pass
def w_tryfin_with_tryfin(mgr, xs):
    try:
        with mgr:
            try:
                return xs[0]
            finally:
                xs.append(1)
    finally:
        xs.append(2)
def w_raise_caught_outside(mgr):
    try:
        with mgr:
            raise ValueError('x')
    except ValueError:
        return 4
