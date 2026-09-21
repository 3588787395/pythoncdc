# -*- coding: utf-8 -*-
# R24 battery case c05_cc_as_statement
# SHAPE: chained comparisons that are *statements*, never ternary conditions -- if/elif/else
#        whose arms are assignments, a chained compare guarding a statement block, a chained
#        compare as a return value, and an ordinary (non-chained) ternary inside a call.
#        These are the shapes a too-loose ternary-header exemption would rewrite into
#        conditional expressions and thereby break.
# EXPECTED: unchanged from HEAD, and byte-identical product under the candidate.
# MARK: CONTROL
# MUST_CONTAIN: if 0 <= a <= 9:
def cc_as_if_condition(a, b):
    if 0 <= a <= 9:
        b = a * 2
    else:
        b = -a
    return b


def cc_as_elif(a, b):
    if 0 < a < 10:
        b = 1
    elif 10 <= a < 20:
        b = 2
    else:
        b = 3
    return b


def cc_as_return(a):
    return 0 < a < 100


def cc_guarding_stmts(a, b):
    if 0 < a < 10:
        b = b + a
    else:
        b = b - a
    return b


def plain_ternary_in_call(c, v):
    return max(v, 0 if c else 1)
