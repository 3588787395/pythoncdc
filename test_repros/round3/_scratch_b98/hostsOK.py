# Source Generated with Decompyle++ (Python version)
# File: hosts.pyc (Python 3.11)

_P = 1
_Q = 0
_R = 2
_M1 = (_P or _Q) and _R
_M2 = _P or _Q and _R
class C:
    C1 = (_P or _Q) and _R
    C2 = _P or _Q and _R
def f_ret(a, b, c):
    return (a or b) and c
def f_assign(a, b, c):
    x = (a or b) and c
    return x
def f_sym(a, b, c):
    return a and (b or c)
def f_pair(a, b, c, d):
    return (a or b) and (c or d)
def f_pair_tail(a, b, c, d, e):
    return (a or b) and (c or d) and e
