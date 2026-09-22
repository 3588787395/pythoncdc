# -*- coding: utf-8 -*-
"""Round 33 line A synthetic witness family: a `return` whose value must survive an inlined
cleanup copy (a `finally` body and/or a `with` __exit__ call) between the value's production
and the RETURN_VALUE.

Landed (pre-R33-A) readings, recorded on `--arm=landed` before the predicate landed:
  w1_with_tryfinally  47/47 jump 0 true 32   <-- the falsifying witness
  w2/w3/w4/w5         matched                <-- already-passing neighbours of the same family
  c1..c5              matched                <-- controls
So only ``w1`` may flip on a candidate; every other function is a no-regression pin, and the
whole file must read 17/17 once the shape is fixed.

Why w1 and not w2: w2's `try: return / finally:` alone already resolves its chain through a
whitelisted cleanup block, while w1's normal-path cleanup block is the CPython 3.11
method-call sequence `LOAD_FAST/LOAD_METHOD/PRECALL/CALL/POP_TOP` — stack-neutral, terminated
by POP_TOP, but outside the opname whitelist, so the chain walk gave up and the value was
demoted to an expression statement (function returned None).

compiled with an explicit cfile (see scripts note in rounds/round33); nothing here depends on
the corpus.
"""


class Res:
    def read(self):
        return 1

    def dispose(self):
        return None

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def cleanup():
    return None


# ---------------- witnesses: `return` value held across an inlined cleanup ----------------
def w1_with_tryfinally(path):
    with open(path, encoding='utf-8') as f:
        r = Res()
        try:
            return r.read()
        finally:
            r.dispose()


def w2_tryfinally():
    r = Res()
    try:
        return r.read()
    finally:
        r.dispose()


def w3_tryfinally_globalcall():
    r = Res()
    try:
        return r.read()
    finally:
        cleanup()


def w4_tryfinally_nested_value():
    r = Res()
    try:
        return [r.read(), r.read()]
    finally:
        r.dispose()


def w5_with_only_return():
    with Res() as r:
        return r.read()


# ---------------- controls: value genuinely discarded, or return without cleanup ----------------
def c1_no_return_in_try():
    r = Res()
    try:
        r.read()
    finally:
        r.dispose()
    return None


def c2_return_without_finally():
    r = Res()
    try:
        return r.read()
    except OSError:
        return None


def c3_plain_discard():
    r = Res()
    r.read()
    return None


def c4_finally_pass():
    r = Res()
    try:
        return r.read()
    finally:
        pass


def c5_return_before_try():
    r = Res()
    v = r.read()
    try:
        cleanup()
    finally:
        r.dispose()
    return v
