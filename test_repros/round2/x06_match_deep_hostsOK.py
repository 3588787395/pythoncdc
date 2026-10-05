# Source Generated with Decompyle++ (Python version)
# File: x06_match_deep_hosts.pyc (Python 3.11)

__doc__ = 'x06: Match as innermost leaf, host depth >= 3.'
def match_in_if():
    if 1 == 1:
        if 2 == 2:
            R = 2
        else:
            pass
    return 1
def match_in_for():
    for i in range(1):
        if i == 0:
            for j in range(1):
                if j == 0:
                    R = j
                    continue
    return 2
def match_in_try():
    try:
        if 1 == 1:
            try:
                if 2 == 2:
                    R = 2
            finally:
                F = 1
    except ValueError:
        R = 0
    return 3
def match_in_with():
    with _A() as a:
        if 1 == 1:
            with _A() as b:
                if 2 == 2:
                    R = (a, b)
    return 4
def match_in_while():
    if 1 == 1:
        if 2 == 2:
            R = 2
        while False:
            pass
    return 5
def match_shallow():
    if 1 == 1:
        R = 1
    else:
        R = 2
    return 0
