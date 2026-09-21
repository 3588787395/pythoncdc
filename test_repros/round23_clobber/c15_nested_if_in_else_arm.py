# -*- coding: utf-8 -*-
# R23 battery case c15_nested_if_in_else_arm
# SHAPE: nested if inside the ELSE arm of an if whose condition is a plain compare.
# EXPECTED: control.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: CONTROL
def f(a, b, e):
    if a > b:
        return 1
    else:
        if e:
            return 2
        return 3
