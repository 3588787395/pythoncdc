# Source Generated with Decompyle++ (Python version)
# File: nx01_shallow_hosts.pyc (Python 3.11)

__doc__ = 'nx01: six hosts at depth 1, shallow equivalent negative control.'
def s_if():
    R = 1
    return 1
def s_for():
    for i in range(1):
        R = i
    return 2
def s_while():
    return 3
def s_try():
    try:
        R = 1
    except ValueError:
        R = 2
    finally:
        F = 3
    return 4
def s_with():
    with _A() as a:
        R = a
    return 5
def s_match():
    if 1 == 1:
        R = 1
    else:
        R = 2
    return 6
