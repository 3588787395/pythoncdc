"""x10: ExceptHandler bodies as deep hosts."""
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
                        break
    except (TypeError, KeyError) as e2:
        with _A():
            match e2:
                case TypeError():
                    R = 't'
                case _:
                    R = 'o'
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
