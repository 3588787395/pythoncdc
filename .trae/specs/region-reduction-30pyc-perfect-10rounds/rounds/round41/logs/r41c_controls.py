# -*- coding: utf-8 -*-
"""Round 41 negative controls for R41-B -- each must stay CLEAN on both arms.

* r41c_1_natural_tail -- the if IS the last statement of the loop body: merge_block == loop
  header, so the For node regenerates the back edge and an explicit `continue` would add a
  second JUMP_BACKWARD.  This is the term ② exclusion; it is what keeps the predicate from
  over-firing on the common shape.
* r41c_2_break_tail   -- arm tail escapes with `break` after a statement (BREAK role, other site).
* r41c_3_outer_tail   -- continue of an INNER loop whose outer body then continues.
* r41c_4_two_arms     -- both arms of the if carry an escaping tail with statements.
* r41c_5_while        -- while-loop variant with a statement after the if.
* r41c_6_elif         -- continue inside an elif chain arm, body continues afterwards.
"""


def r41c_1_natural_tail(seq, t, acc):
    for x in seq:
        if x != t:
            acc.append(x)
            continue
    return acc


def r41c_2_break_tail(seq, t, acc):
    for x in seq:
        if x == t:
            acc.append(x)
            break
        acc.append(-x)
    return acc


def r41c_3_outer_tail(inner, outer, t, acc):
    for y in outer:
        for x in inner:
            if x == t:
                acc.append(x)
                continue
            acc.append(-x)
        acc.append(y)
    return acc


def r41c_4_two_arms(seq, t, a, b):
    for x in seq:
        if x > 0:
            a.append(x)
            continue
        b.append(x)
        continue
    return a, b


def r41c_5_while(i, acc):
    while i:
        if i == 3:
            acc.append(i)
            i -= 1
            continue
        acc.append(-i)
        i -= 1
    return acc


def r41c_6_elif(seq, t, a, b, c):
    for x in seq:
        if x == t:
            a.append(x)
            continue
        elif x > 0:
            b.append(x)
            continue
        c.append(x)
    return a, b, c
