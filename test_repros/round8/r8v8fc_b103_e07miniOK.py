# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b103_e07mini.pyc (Python 3.11)

def inner(x):
    match x:
        case [a, b] if a > b:
            return a
        case [a, b]:
            return b
        case a if a is not None:
            return a
        case _:
            return 0
