# -*- coding: utf-8 -*-
# R23 battery case d16_twin_conditions_sibling_arms
# SHAPE: Q2 probe: two sibling arms carrying TEXTUALLY IDENTICAL compare tests whose bodies differ only by jump targets (difflib-ambiguous alignment family).
# EXPECTED: control: emission order must follow offset order.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: DIAG
def g1(x):
    return x + 1


def f(flag, a, b, k):
    if flag:
        if a > k:
            if b <= k or a == b:
                g1(a)
            elif a < k:
                g1(b)
        if b > k:
            g1(k)
        return 1
    elif a > k:
        return 2
    return 0
