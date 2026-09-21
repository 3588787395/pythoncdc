# -*- coding: utf-8 -*-
# R23 battery case b09_outer_body_stmt_then_inner_if
# SHAPE: same merged-block situation with an inner IF instead of a while (isolates loop-specific code).
# EXPECTED: leading assignment emitted.
# ACTUAL-HEAD: OK |d|=0 
# ACTUAL-C1A: OK |d|=0 
# MARK: DIAG
# MUST_CONTAIN: dt = tick()
def tick():
    return 1


def f(active, last, n):
    dt = n
    while active:
        dt = tick()
        if dt <= last:
            n = n + 1
        n = n + dt
    return n
