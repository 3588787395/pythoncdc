# -*- coding: utf-8 -*-
"""r67-diag3 synthetic repro: an explicit `continue` that terminates the LAST arm
of an if/elif chain inside a loop body is elided by the generator, losing CPython's
second unconditional back edge."""


def c1(xs):
    d = {}
    for x in xs:
        if x == 1:
            d[x] = 1
        elif x == 2:
            d[x] = 2
        elif x is not None:
            d[x] = 3
        else:
            d[x] = 4
            continue
    return d


def c2(xs):
    d = {}
    for x in xs:
        if x == 1:
            d[x] = 1
        else:
            d[x] = 2
            continue
    return d


def c3(xs):
    d = {}
    for x in xs:
        if x == 1:
            d[x] = 1
            continue
        d[x] = 2
    return d


def c4(xs):
    n = 0
    while n < 9:
        n += 1
        if n == 1:
            continue
        elif n == 2:
            n += 1
            continue
    return n
