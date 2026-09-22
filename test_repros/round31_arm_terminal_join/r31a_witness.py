# -*- coding: utf-8 -*-
"""Round 31 G0 witness (line A, R31-B/R31-C): a nested-if arm whose join block is itself a
terminal hard-exit statement block (bare `raise`, no normal successor), reached inside an
`except ... as e` handler arm.

Same structural reason as `site-packages/fly/common/flytools.pyc ::
<module>.FileLock.acquire` (official ruler 88/85, jump_diffs=2, true_diffs=14).

Measured readings, both cores run through the mirror harness in `D:/Temp/r31gate/c1`:
  landed core (7ee4151d31faf41b8202)   -> 1/4  w_a 52/47 j4 t11 | w_b 48/44 j3 t14
                                                 | w_c 64/63 j2 t51
  R31-C (site 1 + elif-chain replay)    -> 3/4  w_a and w_b matched; w_c unchanged
  R31-B (site 1 only)                   -> 2/4  only w_b matched
So w_a/w_b are the predicate's own witnesses (they FAIL on the landed core and the site-2
replay is what brings w_a back), while w_c is a distinct residual shape that this predicate
deliberately does not reach.
"""



def w_a_handler_raise_after_nested_if(v):
    start = 0
    while True:
        try:
            start = start + len(v)
            break
        except ValueError as e:
            if e.args != ():
                if start > 2:
                    start = 0
                raise
            if start > 7:
                raise RuntimeError('t')
            start = start + 1
    return None


def w_b_handler_raise_then_fall(v):
    total = 0
    while v:
        try:
            total = total + 1
        except KeyError as e:
            if e.args != ():
                if total > 2:
                    total = 0
                raise
            total = total + 5
    return total


def w_c_handler_nested_raise_deep(v):
    acc = 0
    while v:
        try:
            acc = acc + 1
            if acc == 3:
                break
        except TypeError as e:
            if e.args != ():
                if acc > 4:
                    if v:
                        acc = 0
                    raise
                acc = acc + 2
            else:
                acc = acc + 9
        v = v - 1
    return acc
