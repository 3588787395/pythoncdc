# -*- coding: utf-8 -*-
# R24 battery case c04_cc_ternary_nested_in_loop
# SHAPE: the same nested chained-compare ternary assignment, but the enclosing guard sits
#        inside a `for` body, so the region whose entry is the ternary header is two
#        levels deep (loop region -> if region).  Mirrors the corpus twins' loop bodies.
# EXPECTED: one ternary assignment statement, loop back-edge preserved.
# ACTUAL-HEAD: FAIL official 1/2 -- `loop_guard` 30 -> 25 instructions; the loop body's
#              ternary is dropped along with the assignment.
# ACTUAL-CAND: FAIL identically, product sha identical to HEAD (measured ccd1f99c2c0ccbce on
#              both cores), so R24-A neither reaches nor disturbs the loop-nested shape.
# MARK: PRED_R24A_STABLE
# MUST_CONTAIN: total = total + (1 if 0 < n < 10 else 2)
def loop_guard(notes):
    total = 0
    for n in notes:
        if n:
            total = total + (1 if 0 < n < 10 else 2)
    return total
