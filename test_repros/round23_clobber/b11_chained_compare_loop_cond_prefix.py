# -*- coding: utf-8 -*-
# R23 battery case b11_chained_compare_loop_cond_prefix
# SHAPE: merged condition block whose prefix is a statement, condition is a SWAP/COPY chained compare (the shape realtime_event_source gets right on the inner loop only).
# EXPECTED: leading assignment emitted, chain compare preserved.
# ACTUAL-HEAD: FAIL |d|=3 f seq_len orig=42 decomp=39
# ACTUAL-C1A: FAIL |d|=3 f seq_len orig=42 decomp=39
# MARK: DIAG
# MUST_CONTAIN: dt = tick()
def tick():
    return 1


def f(active, lo, hi, n):
    dt = n
    while active:
        dt = tick()
        while lo < dt < hi:
            dt = tick()
        n = n + dt
    return n
