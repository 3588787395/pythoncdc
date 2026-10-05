# Source Generated with Decompyle++ (Python version)
# File: x02_for_deep_hosts.pyc (Python 3.11)

__doc__ = 'x02: For as innermost leaf, host depth >= 3.'
def for_in_if():
    for i in range(1):
        for j in range(1):
            R = j
    return 1
def for_in_while():
    for i in range(1):
        for j in range(1):
            R = j
    return 2
def for_in_try():
    try:
        for i in range(1):
            try:
                for j in range(1):
                    R = j
            finally:
                F = 1
            for j in range(1):
                pass
    except ValueError:
        R = 2
    return 3
def for_in_with():
    with _A() as a:
        for i in range(1):
            with _A() as b:
                for j in range(1):
                    R = (a, b, j)
    return 4
def for_in_match():
    match (1, 2):
        case [a, b]:
            for i in range(1):
                if not b == 2:
                    continue
                for j in range(1):
                    R = j
        case _:
            return 5
def for_shallow():
    for i in range(1):
        R = i
    return 0
