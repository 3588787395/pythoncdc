# -*- coding: utf-8 -*-
# R23 battery case a02_or_ext_chained_cmp_minimal
# SHAPE: ddmin-minimal (r23fix/dd/g6.txt): chained comparison on the or-left, nested If in the arm.
# EXPECTED: if-arm body keeps its nested `if a: return None` (HEAD reduces it to `pass`).
# ACTUAL-HEAD: FAIL |d|=6 f seq_len orig=31 decomp=25
# ACTUAL-C1A: FAIL |d|=6 f seq_len orig=31 decomp=25
# MARK: DIAG_OR_EXT_NOEFFECT
# MUST_CONTAIN: elif x > lo:
def log(m):
    return None


def f(lo, x, hi, p, q, e, a):
    if lo <= x < hi or p == q:
        if e:
            if a:
                return None
    elif x > lo:
        return 3
    return 0
