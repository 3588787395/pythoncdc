# -*- coding: utf-8 -*-
# Attempt at a minimal repro of c1's mechanism (upstream BoolOpRegion whose merge_block
# is the entry of a SAME-LEVEL sibling region, which the landed dispatch never releases).
def sib_a(t, u, v, w):
    x = t or u
    y = v or w
    return x + y


def sib_b(t, u, n):
    x = t or u
    z = int(n or 1)
    return (x, z)


def sib_c(s, p):
    e = s or p
    f = (e[0:8] or '1530')
    return int(f)
