# -*- coding: utf-8 -*-
"""Round 31 G0 CONTROL battery: near-miss shapes around the R31-B/R31-C arm-stop release.

c1  nested one-arm if whose join block is an ordinary continuation (not terminal)
c2  arm tail is a `break` (last instruction is a forward jump, not an exit op)
c3  bare raise as the whole handler tail, no nested if join before it
c4  raise INSIDE the nested if body (the nested if's join is not the raise)
c5  nested-if terminal join inside a plain (non-handler) loop body arm
c6  nested-if terminal join where BOTH arms of the outer if end in the raise

Measured readings (mirror harness, `D:/Temp/r31gate/c1`): this file reads 5/7 on the landed
core AND 5/7 under R31-B and R31-C, with the two failures being the same pair on all three
cores -- `c2_arm_tail_is_break` 51/49 j1 t16 and `c6_both_arms_end_in_raise` 46/52 j4 t19,
i.e. pre-existing defects of other families, NOT regressions caused here.  The shipping
criterion for this file is therefore sha-level: its product is byte-identical head vs R31-C
(`SAME` in the A/B), which is what proves the predicate does not fire on any of the six
neighbour positions.
"""



def c1_join_is_continuation(v):
    total = 0
    while v:
        try:
            total = total + 1
        except KeyError as e:
            if e.args != ():
                if total > 2:
                    total = 0
                total = total + 3
            total = total + 4
        v = v - 1
    return total


def c2_arm_tail_is_break(v):
    n = 0
    while True:
        try:
            n = n + len(v)
        except ValueError as e:
            if e.args != ():
                if n > 2:
                    n = 0
                break
            n = n + 1
    return n


def c3_raise_is_whole_handler_tail(v):
    n = 0
    while v:
        try:
            n = n + 1
        except OSError as e:
            n = n + 2
            raise
        v = v - 1
    return n


def c4_raise_inside_nested_body(v):
    n = 0
    while v:
        try:
            n = n + 1
        except OSError as e:
            if e.args != ():
                if n > 2:
                    raise
                n = n + 3
            n = n + 4
        v = v - 1
    return n


def c5_plain_loop_body_arm(v):
    n = 0
    while v:
        if v != 1:
            if n > 2:
                n = 0
            raise ValueError('a')
        n = n + 1
        v = v - 1
    return n


def c6_both_arms_end_in_raise(v):
    n = 0
    while v:
        try:
            n = n + 1
        except IndexError as e:
            if e.args != ():
                if n > 2:
                    n = 0
                raise
            else:
                if n > 5:
                    n = 9
                raise
    return n
