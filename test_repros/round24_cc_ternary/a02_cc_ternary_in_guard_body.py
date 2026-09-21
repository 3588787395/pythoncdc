# -*- coding: utf-8 -*-
# R24 battery case a02_cc_ternary_in_guard_body
# SHAPE: minimal single-statement reduction of a01 -- a chained-compare ternary assignment
#        as the only statement of an `if` body.
# EXPECTED: `lo = 1 if 0 < v < 10 else 2`.
# ACTUAL-HEAD: FAIL -- assignment dropped, arms emitted as bare expressions.  official 1/2.
# ACTUAL-CAND: OK   -- official 2/2.
# MARK: PRED_R24A_FIX
# MUST_CONTAIN: lo = 1 if 0 < v < 10 else 2
def f02(v, lo, hi):
    if v:
        lo = 1 if 0 < v < 10 else 2
    return lo
