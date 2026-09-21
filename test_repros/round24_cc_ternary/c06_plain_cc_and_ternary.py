# -*- coding: utf-8 -*-
# R24 battery case c06_plain_cc_and_ternary
# SHAPE: the rest of the neighbourhood that must not move -- chained compare inside a
#        boolean condition, an ordinary ternary whose arms are values, a chained compare
#        guarding an assignment followed by a *plain* ternary return.
# EXPECTED: unchanged; byte-identical product under the candidate.
# ACTUAL-HEAD: FAIL official 1/5 -- four of these five functions carry pre-existing defects
#              (`plain_cc_if` 57->59, `cc_in_bool` 21->32, `cc_as_value` 21->23,
#              `plain_ternaries` 34->31).  They are *not* what R24-A addresses.
# ACTUAL-CAND: FAIL the same 1/5 with product sha identical to HEAD (b492e3523458fdb9 both).
#              Recorded as evidence that R24-A leaves the chained-compare-as-statement and
#              plain-ternary families exactly as they are.
# MARK: PRED_R24A_STABLE
# MUST_CONTAIN: if 0 < a < 10:
def plain_cc_if(a, b):
    if 0 < a < 10:
        b = b + 1
    elif 10 <= a < 20:
        b = b + 2
    else:
        b = b + 3
    if 0 < a <= 5:
        b -= 1
    return b


def plain_ternaries(c, x):
    y = 1 if c else 2
    z = x if x > 0 else -x
    w = [x if c else -x, (1 if c else 2)]
    return y, z, w


def cc_in_bool(a, b, c):
    return 0 < a < 10 and b > c or a == b


def cc_as_value(a, b):
    if 0 < a < 10:
        b = 1
    return b if b else 0
