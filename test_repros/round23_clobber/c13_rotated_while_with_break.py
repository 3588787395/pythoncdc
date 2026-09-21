# -*- coding: utf-8 -*-
# R23 battery case c13_rotated_while_with_break
# SHAPE: rotated while with a break in the body.
# EXPECTED: control.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: CONTROL
def f(active, n):
    while active:
        n = n + 1
        if n > 3:
            break
    return n
