# -*- coding: utf-8 -*-
# R23 battery case b10_plain_while_body_leading_store
# SHAPE: outer while body opens with a STORE whose block is merged with the loop's own re-test (works today; the emission is done by the body sweep, not the condition path).
# EXPECTED: control: statement emitted, unchanged by R23-A.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: CONTROL
def tick():
    return 1


def f(active, n):
    while active:
        n = tick()
        if n > 1:
            active = False
    return n
