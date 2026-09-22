# -*- coding: utf-8 -*-
def s(n):
    return n


def f(dt):
    if dt == 'a':
        if dt > '08:30' or dt < '07:00':
            s(1)
        elif dt > '09:00' or dt < '06:30':
            s(2)
    elif dt == 'b':
        s(4)
    s(0)
    return None
