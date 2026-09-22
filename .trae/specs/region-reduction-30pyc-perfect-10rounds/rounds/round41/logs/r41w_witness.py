# -*- coding: utf-8 -*-
"""Round 41 witnesses for R41-B -- each must be DEFECT on landed bytes, CLEAN on R41-B.

The shape: a CONTINUE-role block that still carries meaningful statements sits inside an
if-arm, and the loop body has more code after that if (IfRegion.merge_block is not the
loop header).  Its JUMP_BACKWARD is a real, separate edge -- the For node's implicit back
edge belongs to the block that follows, so the arm tail must carry an explicit `continue`.

* r41w_1_mid_arm      -- minimal: arm tail `acc.append(v)` + continue, one statement after the if.
* r41w_2_guard_break  -- a `break` earlier in the same arm (the corpus function's shape: the
                         arm has both break tails and the escaping tail).
* r41w_3_or_cond      -- the arm condition is an or-chain (corpus: `if a >= 16 or a < 9`).
"""


def r41w_1_mid_arm(seq, t, acc, rest):
    for i, v in seq:
        if i == t:
            acc.append(v)
            continue
        rest.append(v)
    return acc, rest


def r41w_2_guard_break(seq, t, acc):
    for i, v in seq:
        if i == t:
            if v < 0:
                break
            acc.append(v)
            continue
        acc.append(-v)
    return acc


def r41w_3_or_cond(seq, lo, hi, acc, rest):
    for x in seq:
        if x >= hi or x <= lo:
            acc.append(x)
            continue
        rest.append(x)
    return acc, rest
