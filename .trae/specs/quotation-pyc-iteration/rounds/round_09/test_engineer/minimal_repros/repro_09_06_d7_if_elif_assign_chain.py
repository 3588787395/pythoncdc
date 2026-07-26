"""Repro 09-06: D7 (P2) if/elif/elif/elif assign chain compressed to ternary.

The quotation.pyc::build_future_fill_time line 351 defect collapses an
if/elif/elif/elif assignment chain (4 branches) into a single bare Expr
of nested ternary of `==`:
    if x == 1:
        y = 'a'
    elif x == 2:
        y = 'b'
    elif x == 3:
        y = 'c'
    else:
        y = 'd'
becomes:
    y == 'a' if x == 1 else y == 'b' if x == 2 else y == 'c' if x == 3 else x == 4

R8 repro_08_03 confirmed D7 fires with 4+ branches. A 3-branch chain
(repro_09_06 v1) did NOT fire (NOT-REPRO). This repro uses 4 branches
to reliably trigger D7.

Expected defect: a single bare Expr of nested ternary of `==`.
"""


def classify(x):
    if x == 1:
        y = 'a'
    elif x == 2:
        y = 'b'
    elif x == 3:
        y = 'c'
    else:
        y = 'd'
    return y
