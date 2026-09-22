# -*- coding: utf-8 -*-
def s(n):
    return n


def f(dt):
    if dt == 'a':
        if '08:30' <= dt < '08:59':
            s(1)
        elif '08:59' <= dt < '09:00':
            s(2)
    elif dt == 'b':
        s(3)
    s(0)
    return None
