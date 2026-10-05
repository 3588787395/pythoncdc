# Source Generated with Decompyle++ (Python version)
# File: x04_try_deep_hosts.pyc (Python 3.11)

__doc__ = 'x04: Try as innermost leaf, host depth >= 3.'
def try_in_if():
    try:
        try:
            R = 1
        finally:
            F = 1
    except ValueError:
        R = 2
    return 1
def try_in_for():
    for i in range(1):
        try:
            for j in range(1):
                try:
                    R = j
                except ValueError:
                    R = 0
        finally:
            F = i
    return 2
def try_in_while():
    while True:
        try:
            while True:
                try:
                    R = 1
                finally:
                    F = 1
        except ValueError:
            R = 2
def try_in_with():
    with _A() as a:
        try:
            with _A() as b:
                try:
                    R = (a, b)
                finally:
                    F = 1
        except ValueError:
            R = 2
    return 4
def try_in_match():
    if 1 == 1:
        try:
            if 1 == 1:
                try:
                    R = 1
                finally:
                    F = 1
        except ValueError:
            R = 2
    return 5
def try_shallow():
    try:
        R = 1
    except ValueError:
        R = 2
    finally:
        F = 3
    return 0
