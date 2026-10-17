# Source Generated with Decompyle++ (Python version)
# File: rec1_x10_x10_handler_hosts.pyc (Python 3.11)

__doc__ = 'x10: ExceptHandler bodies as deep hosts.'
def h_basic():
    try:
        X = 1
    except ValueError as e:
        for i in range(2):
            if i:
                while i:
                    try:
                        i -= 1
                    except ValueError:
                        pass
    except (TypeError, KeyError) as e2:
        with _A():
            match e2:
                case TypeError():
                    pass
                case _:
                    pass
    else:
        E = 0
    finally:
        F = 9
    return X
def h_shallow():
    try:
        X = 1
    except ValueError:
        R = 2
    return X
