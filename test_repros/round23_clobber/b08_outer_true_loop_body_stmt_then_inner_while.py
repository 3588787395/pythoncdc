# -*- coding: utf-8 -*-
# R23 battery case b08_outer_true_loop_body_stmt_then_inner_while
# SHAPE: same as b07 but the outer loop is `while True:` (the exact clock_worker nesting depth).
# EXPECTED: leading assignment emitted once per statement, no duplicated loop header.
# ACTUAL-HEAD: FAIL |d|=3 f seq_len orig=27 decomp=24
# ACTUAL-C1A: FAIL |d|=3 f seq_len orig=27 decomp=24
# MARK: DIAG
def tick():
    return 1


def f(active, last, n):
    dt = n
    while True:
        while active:
            dt = tick()
            while dt <= last:
                dt = tick()
            n = n + dt
        break
    return n
