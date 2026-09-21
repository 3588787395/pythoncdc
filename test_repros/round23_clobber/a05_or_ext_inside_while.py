# -*- coding: utf-8 -*-
# R23 battery case a05_or_ext_inside_while
# SHAPE: or-extended if nested in a while, then-arm reduces a nested if (rotated loop context).
# EXPECTED: loop + both arms emitted.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: DIAG_OR_EXT_NOEFFECT
# MUST_CONTAIN: elif a < b:
def log(m):
    return None


def f(a, b, c, d, e):
    while a:
        if a > b or c == d:
            if e:
                if b:
                    return None
        elif a < b:
            return 3
        a = a - 1
    return 0
