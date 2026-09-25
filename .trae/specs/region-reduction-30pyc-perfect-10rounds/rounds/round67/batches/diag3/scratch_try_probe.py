# -*- coding: utf-8 -*-
"""probe: hunt the CPython-3.11 double-back-edge layout (try body ending in an
if/elif chain, inside a loop) that klinedata.get_all_real_daily_kline shows."""
import sys

sys.setrecursionlimit(1000)


def k1(xs):
    d = {}
    for x in xs:
        try:
            if x == 1:
                d[x] = 1
            elif x == 2:
                d[x] = 2
            else:
                d[x] = 4
        except BaseException:
            pass
    return d


def k2(xs):
    d = {}
    for x in xs:
        try:
            if x == 1:
                d[x] = 1
            elif x is not None:
                d[x] = 3
            else:
                d[x] = 4
        except BaseException:
            d[x] = 0
    return d


def k3(xs):
    d = {}
    for x in xs:
        try:
            for y in x:
                if y == 1:
                    d[y] = 1
                elif y == 2:
                    d[y] = 2
                else:
                    d[y] = 4
        except BaseException:
            pass
    return d


def k4(xs):
    d = {}
    for x in xs:
        if x == 1:
            d[x] = 1
        elif x == 2:
            d[x] = 2
        else:
            try:
                if x is not None:
                    d[x] = 3
                else:
                    d[x] = 4
            except BaseException:
                pass
    return d


def k5(xs):
    d = {}
    for x in xs:
        try:
            try:
                if x == 1:
                    d[x] = 1
                elif x is not None:
                    d[x] = 3
                else:
                    d[x] = 4
            except BaseException:
                pass
        except BaseException:
            pass
    return d
