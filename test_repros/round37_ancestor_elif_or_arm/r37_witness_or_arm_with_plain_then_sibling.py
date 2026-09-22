# -*- coding: utf-8 -*-
def s(n):
    return n


def f(dt):
    if dt == 'a':
        if '08:30' <= dt < '08:59' or '12:30' <= dt < '12:59':
            s(1)
        elif dt == 'q':
            s(2)
    elif dt == 'b':
        s(4)
    s(0)
    return None
