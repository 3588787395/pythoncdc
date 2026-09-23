# -*- coding: utf-8 -*-
"""Round 48 line A witnesses: a function-level shared tail `return <var>` block
reached both by an explicit forward jump (end of the then arm) and by
fall-through (end of the else arm) -- the shape of
site-packages/IQCommon/api/klinedata.pyc :: <module>.get_history_new
and <module>.get_multiminute_his_data.
"""


def w48_01_plain_if_else_shared_return(symbols, freq):
    if freq == 1:
        k = {'a': 1}
    else:
        k = symbols
    return k


def w48_02_arm_loop_nested_if_shared_return(symbols, count, freq):
    k = {}
    if count > 0:
        d = {}
        for s in symbols:
            if s in d:
                d[s] = 1
            else:
                d[s] = 2
        if freq == 1:
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


def w48_03_shared_return_none(symbols, count, freq):
    k = {}
    if count > 0:
        d = {}
        for s in symbols:
            if s in d:
                d[s] = 1
            else:
                d[s] = 2
        if freq == 1:
            k = d
        else:
            k = symbols
    else:
        if freq in (2, 3):
            h = len(symbols)
        else:
            h = count
        k = h
    return


def w48_04_single_pred_tail(symbols, count, freq):
    k = {}
    if count > 0:
        d = {}
        for s in symbols:
            if s in d:
                d[s] = 1
            else:
                d[s] = 2
        if freq == 1:
            k = d
        else:
            k = symbols
        return k
    if freq in (2, 3):
        h = len(symbols)
    else:
        h = count
    k = h
    return k
