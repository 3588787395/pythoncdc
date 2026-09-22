# -*- coding: utf-8 -*-
"""Round 40 negative controls for R40-A2 -- each must stay CLEAN on both arms.

* r40c_1_two_tails  -- the then arm has TWO tails: one escapes to the header, the other
  falls through into the merge block.  The merge block really is a join, so the predicate
  must NOT fire (this is what separates "some tail escapes" from "every tail escapes").
* r40c_2_elif       -- escape followed by an elif chain hanging off the same merge point.
* r40c_3_break      -- then arm escapes the loop with `break`, not `continue`.
* r40c_5_merge_join -- both arms fall through into a merge block that is followed by more
  statements inside the body: the classic true merge.
* r40c_plain / r40c_cont / r40c_noelse / r40c_and / r40c_while -- the round-39 baseline
  shapes for this gate's neighbourhood (purity-only promotion, implicit tail continue).
"""


def r40c_plain(seq, d):
    for x in seq:
        if x > 0:
            d['a'] = 1
        else:
            d['a'] = 2
    return d


def r40c_1_two_tails(seq, d):
    for x in seq:
        if x > 0:
            if x > 10:
                d['a'] = 1
                continue
            d['b'] = 2
        else:
            d['a'] = 3
        d['c'] = 4
    return d


def r40c_2_elif(seq, d):
    for x in seq:
        if x > 0:
            d['a'] = 1
            continue
        elif x < -5:
            d['a'] = 2
        d['c'] = 4
    return d


def r40c_3_break(i, d):
    while i:
        if i == 1 or i == 2:
            d['a'] = 0
            break
        i -= 1
    return d


def r40c_5_merge_join(seq, d):
    for x in seq:
        if x == 1 or x == 2:
            d['a'] = 0
        else:
            d['a'] = 1
        d['b'] = x
    return d


def r40c_cont(seq, d):
    for x in seq:
        if x > 0:
            d['a'] = 1
            continue
        d['a'] = 2
    return d


def r40c_noelse(seq, d):
    for x in seq:
        if x > 0:
            d['a'] = 1
        d['b'] = 2
    return d


def r40c_and(seq, d):
    for x in seq:
        if x > 0 and x < 5:
            d['a'] = 0
        else:
            d['a'] = 1
    return d


def r40c_while(a, d):
    i = 0
    while i < a:
        if i == 1 or i == 2:
            d['a'] = 0
        else:
            d['a'] = 1
        i += 1
    return d
