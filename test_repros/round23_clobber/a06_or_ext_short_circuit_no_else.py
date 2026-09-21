# -*- coding: utf-8 -*-
# R23 battery case a06_or_ext_short_circuit_no_else
# SHAPE: or-extended if with NO else arm (the W20 collapse-guard shape; _or_else_block is None).
# EXPECTED: no collapse: body must stay non-empty.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: CONTROL
# MUST_CONTAIN: return 1
def log(m):
    return None


def f(a, b, c, d):
    if a > b or c == d:
        return 1
    return 0
