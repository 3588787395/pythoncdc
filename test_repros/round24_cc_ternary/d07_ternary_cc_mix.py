# -*- coding: utf-8 -*-
# R24 battery case d07_ternary_cc_mix
# SHAPE: diagnostics only.  Shapes adjacent to R24-A where the candidate *does* change the
#        product but the official matched count is unchanged on HEAD (a nested ternary whose
#        outer condition is a plain test and inner one is a chained compare, and a chained
#        compare nested in an `and`).  Recorded so the round doc can state exactly which
#        products R24-A rewrites without any currency change.
# EXPECTED: OK on both cores; product may differ (this case is NOT under gate G4).
# ACTUAL-HEAD: FAIL official 2/4 -- `cc_in_boolop` 31->29 (over-emission) and
#              `ternary_with_cc_arms` 23->21.
# ACTUAL-CAND: FAIL official 2/4, product sha CHANGES (694390b77a4d0335 -> a023a140ce5c29c8,
#              379 -> 339 bytes) and `ternary_with_cc_arms` becomes length-correct 23/23,
#              but the function is still not matched, so no currency.  This is one of the two
#              corpus-wide products R24-A rewrites without an official gain.
# MARK: DIAG
def ternary_with_cc_arms(a, b):
    x = (1 if 0 < a < 5 else 2) if b else 3
    return x


def cc_in_boolop(a, b, c):
    if (0 < a < 10) and (b < c < b + 10):
        return 1
    return 0


def ret_cc(a):
    return 0 < a < 100
