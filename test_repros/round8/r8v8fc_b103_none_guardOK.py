# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b103_none_guard.pyc (Python 3.11)

def n3(x):
    match x:
        case a if a is not None:
            return a
        case a if a is None:
            return 0
        case _:
            return 1
