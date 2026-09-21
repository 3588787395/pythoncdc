# -*- coding: utf-8 -*-
# R23 battery case c12_plain_if_elif_chain
# SHAPE: plain if/elif/else chain, no boolop in any condition.
# EXPECTED: control.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: CONTROL
def f(a, b):
    if a > b:
        return 1
    elif a == b:
        return 2
    return 3
