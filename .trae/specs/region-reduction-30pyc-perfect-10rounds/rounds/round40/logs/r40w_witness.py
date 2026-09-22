# -*- coding: utf-8 -*-
"""Round 40 witnesses for R40-A2 (merge_block that is not a merge).

Shape family: inside a loop, `if <or/and condition>: A else: B` where BOTH arms end by
jumping back to the loop header.  The region analyzer still hands the generator an
IfRegion whose `merge_block` is the loop's natural back-edge block; because that block
carries the else arm's own statements it is not "pure", so the purity-only promotion
`if not _mb_meaningful:` refuses, `orelse` freezes to None, and the two tail
JUMP_BACKWARDs collapse into one on recompilation (one instruction short).

Every function below decompiles `seq_len` DEFECT on the pre-R40 core and CLEAN after.
"""


def r40w_s2_or(seq, d):
    for x in seq:
        if x == 1 or x == 2:
            d['a'] = 0
        else:
            d['a'] = 1
    return d


def r40w_s7_nested(seq, d):
    for x in seq:
        for y in x:
            if y == 1 or y == 2:
                d['a'] = 0
            else:
                d['a'] = 1
    return d


def r40w_c4_inner_continue(seq, d):
    for x in seq:
        for y in x:
            if y == 1 or y == 2:
                d['a'] = 1
                continue
            d['b'] = 2
    return d
