# Source Generated with Decompyle++ (Python version)
# File: x05_with_deep_hosts.pyc (Python 3.11)

__doc__ = 'x05: With as innermost leaf, host depth >= 3.'
def with_in_if():
    with _A() as a, _A() as b:
        R = (a, b)
    return 1
def with_in_for():
    for i in range(1):
        with _A() as a, _A() as b:
            R = (i, a, b)
    return 2
def with_in_try():
    try:
        with _A() as a:
            try:
                with _A() as b:
                    R = (a, b)
            finally:
                F = 1
    except ValueError:
        R = 2
    return 3
def with_in_while():
    with _A() as a, _A() as b:
        R = (a, b)
    return 4
def with_in_match():
    if 1 == 1:
        with _A() as a:
            if 1 == 1:
                with _A() as b:
                    with _A() as a:
                        R = (a, b)
    return 5
def with_shallow():
    with _A() as a:
        R = a
    return 0
