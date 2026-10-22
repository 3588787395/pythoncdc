# Source Generated with Decompyle++ (Python version)
# File: cp_match_guard.pyc (Python 3.11)

def f(v):
    match v:
        case 1 if v < 0:
            return 'a'
        case _:
            return 'b'
