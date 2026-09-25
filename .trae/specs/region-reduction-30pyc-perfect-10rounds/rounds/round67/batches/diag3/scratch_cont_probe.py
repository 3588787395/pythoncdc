# -*- coding: utf-8 -*-
"""probe: nested if/else + trailing `continue` inside the LAST arm of an if/elif
chain (mirrors klinedata.get_all_real_daily_kline line 1597)."""


def c5(xs):
    d = {}
    for x in xs:
        if x == 1:
            d[x] = 1
        elif x == 2:
            d[x] = 2
        else:
            if x is not None:
                d[x] = 3
            else:
                d[x] = 4
            continue
    return d


def c6(xs):
    d = {}
    for x in xs:
        if x == 1:
            d[x] = 1
        else:
            if x is not None:
                d[x] = 3
            else:
                d[x] = 4
            continue
    return d


def c7(xs):
    d = {}
    for x in xs:
        if x == 1:
            d[x] = 1
        else:
            d[x] = 4
            continue
    return d


def c8(xs):
    d = {}
    for x in xs:
        if x == 1:
            d[x] = 1
        elif x == 2:
            d[x] = 2
        else:
            d[x] = 4
            continue
    return d
