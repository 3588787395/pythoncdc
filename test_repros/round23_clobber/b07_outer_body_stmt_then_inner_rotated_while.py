# -*- coding: utf-8 -*-
# R23 battery case b07_outer_body_stmt_then_inner_rotated_while
# SHAPE: clock_worker shape: outer rotated while; its body opens with a complete STORE whose block is then MERGED with the inner while's condition test (one basic block, no boundary).
# EXPECTED: the leading assignment is emitted before the inner while (dt is bound).
# ACTUAL-HEAD: FAIL |d|=3 f seq_len orig=27 decomp=24
# ACTUAL-C1A: FAIL |d|=3 f seq_len orig=27 decomp=24
# MARK: DIAG
# MUST_CONTAIN: dt = tick()
def tick():
    return 1


def f(active, last, n):
    dt = n
    while active:
        dt = tick()
        while dt <= last:
            dt = tick()
        n = n + dt
    return n
