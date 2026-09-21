# -*- coding: utf-8 -*-
# R23 battery case a04_or_ext_two_chains_in_series
# SHAPE: two or-extended ifs in series, each with a nested reduction -> second frame must not inherit the first frame's residue.
# EXPECTED: both elif arms present.
# ACTUAL-HEAD: FAIL |d|=2 f seq_len orig=43 decomp=41
# ACTUAL-C1A: FAIL |d|=2 f seq_len orig=43 decomp=41
# MARK: DIAG_OR_EXT_NOEFFECT
# MUST_CONTAIN: return 4
def log(m):
    return None


def f(a, b, c, d, e):
    if a > b or c == d:
        if e:
            if a:
                return None
    elif a < b:
        return 3
    if c > d or a == e:
        if d:
            if b:
                return None
    elif b:
        return 4
    return 0
