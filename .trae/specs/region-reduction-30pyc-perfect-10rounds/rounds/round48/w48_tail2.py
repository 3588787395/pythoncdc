# -*- coding: utf-8 -*-
"""Round 48 line A, second witness set: mimic get_history_new's ingredients --
an outer if/else whose two arms converge on ONE function-level tail
`return kline_data_dict` block, where the THEN arm additionally contains an
early `return` of another value plus a loop with per-iteration exits.
"""


def v48_01_arm_has_early_return(symbols, count, freq):
    if count > 0:
        d = {}
        for s in symbols:
            d[s] = 1
        if freq == 1:
            return d
        for s in symbols:
            if s in d:
                continue
            d[s] = 2
        k = d
    else:
        if freq in (2, 3):
            h = len(symbols)
        else:
            h = count
        k = h
    return k


def v48_02_nested_if_else_in_arm(symbols, count, freq):
    if count > 0:
        d = {}
        for s in symbols:
            if s in d:
                d[s] = 1
                continue
            elif d.get(s):
                d[s] = 2
                continue
        if freq == 1:
            return d
        if freq == 2:
            k = d
        else:
            k = symbols
    else:
        if freq in (2, 3):
            h = len(symbols)
        else:
            h = count
        k = h
    return k


def v48_03_two_level_guard(symbols, count, freq):
    if count > 0:
        if freq == 3:
            g = len(symbols) * 1000000 + 83000
        else:
            g = len(symbols) * 1000000 + 93000
        d = {}
        for s in symbols:
            if s in d:
                continue
            elif len(s) > 0:
                d[s] = g
                continue
            d[s] = 1
        if freq == 1:
            return d
        k = d
    else:
        if freq in (2, 3):
            h = len(symbols)
        else:
            h = count
        k = h
    return k


def v48_04_no_loop_early_return(symbols, count, freq):
    if count > 0:
        d = {}
        if freq == 1:
            return d
        k = d
    else:
        h = len(symbols)
        k = h
    return k
