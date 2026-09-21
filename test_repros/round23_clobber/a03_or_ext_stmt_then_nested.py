# -*- coding: utf-8 -*-
# R23 battery case a03_or_ext_stmt_then_nested
# SHAPE: or-extended if, THEN arm = statement + nested if with sink.
# EXPECTED: whole arm + elif arm emitted.
# ACTUAL-HEAD: FAIL |d|=2 f seq_len orig=30 decomp=28
# ACTUAL-C1A: FAIL |d|=2 f seq_len orig=30 decomp=28
# MARK: DIAG_OR_EXT_NOEFFECT
# MUST_CONTAIN: elif a < b:
def log(m):
    return None


def f(a, b, c, d, e):
    if a > b or c == d:
        if e:
            log(e)
            if a > b:
                return None
    elif a < b:
        return 3
    return 0
