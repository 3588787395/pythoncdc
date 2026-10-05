# Source Generated with Decompyle++ (Python version)
# File: x10_handler_hosts.pyc (Python 3.11)

__doc__ = 'x10: ExceptHandler bodies as deep hosts.'
def h_basic():
    try:
        X = 1
    except ValueError as e:
        for i in range(2):
            while i and i:
                try:
                    i -= 1
                except ValueError:
                    pass
    except (TypeError, KeyError) as e2:
        with _A():
            if True:
                pass
            else:
                R = 'o'
    finally:
        F = 9
    return X
def h_shallow():
    try:
        X = 1
    except ValueError:
        R = 2
    return X
