# Source Generated with Decompyle++ (Python version)
# File: x01_if_deep_hosts.pyc (Python 3.11)

"""x01: If as innermost leaf, host depth >= 3."""
def if_in_for():
    for i in range(1):
        if i:
            for j in range(1):
                if j:
                    R = j
        continue
    return 1
def if_in_while():
    pass
    pass
    while 1:
        if 1:
            R = 1
def if_in_try():
    try:
        if 1:
            try:
                if 1:
                    R = 1
            finally:
                F = 1
    except ValueError:
        R = 2
    return 3
def if_in_with():
    with _A() as a:
        if a:
            with _A() as b:
                if b:
                    R = 1
    return 4
def if_in_match():
    match (1, 2):
        case [a, b]:
            if a and b == 2:
                if b:
                    R = b
            else:
                pass
    return 5
def if_shallow():
    if 1:
        R = 1
    return 0
