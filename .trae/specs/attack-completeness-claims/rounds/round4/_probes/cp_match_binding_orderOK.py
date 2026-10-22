# Source Generated with Decompyle++ (Python version)
# File: cp_match_binding_order.pyc (Python 3.11)

def f(v):
    match v:
        case [a, b]:
            return a - b
        case _:
            return 0
