# -*- coding: utf-8 -*-
# R23 battery case c14_or_in_if_no_nested_reduction
# SHAPE: or-condition if with a FLAT then arm (no nested region to reduce).
# EXPECTED: control: R23-A must be a no-op here.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: CONTROL
def f(a, b, c, d):
    if a > b or c == d:
        return 1
    elif a < b:
        return 3
    return 0
