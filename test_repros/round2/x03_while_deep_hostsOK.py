# Source Generated with Decompyle++ (Python version)
# File: x03_while_deep_hosts.pyc (Python 3.11)

__doc__ = 'x03: While as innermost leaf, host depth >= 3.'
def while_in_if():
    return 1
def while_in_for():
    for i in range(1):
        pass
    return 2
def while_in_try():
    try:
        try:
            pass
        finally:
            F = 1
    except ValueError:
        R = 2
    return 3
def while_in_with():
    with _A() as a, _A() as b:
        pass
    return 4
def while_in_match():
    if 1 == 1:
        if 1 == 1:
            while False:
                pass
            while False:
                pass
        while False:
            pass
    return 5
def while_shallow():
    return 0
