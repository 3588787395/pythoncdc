# -*- coding: utf-8 -*-
"""Round 41 witness set 2 -- the escaping tail block is ALSO the merge block of a nested if.

Distinguishing fact found by tracing the corpus defect (one_prod_to_dataframe): the dropped
JUMP_BACKWARD sits in a CONTINUE-role block that is the merge_block of an immediately nested
IfRegion inside the arm (`if cond: <break-arm>` / `if cond: <stmts>` with no else, whose false
path falls into the escaping block).  The plain arm-tail continue (round41 witness set 1) is
already emitted correctly on landed bytes, so only this merge-escape form may be DEFECT there.
"""


def r41w4_merge_escape(seq, t, acc, rest):
    for i, v in seq:
        if i == t:
            if v < 0:
                acc.append(-1)
            acc.append(v)
            continue
        rest.append(v)
    return acc, rest


def r41w5_break_then_merge_escape(seq, t, acc, rest):
    for i, v in seq:
        if i == t:
            if v < 0:
                break
            acc.append(v)
            continue
        rest.append(v)
    return acc, rest
