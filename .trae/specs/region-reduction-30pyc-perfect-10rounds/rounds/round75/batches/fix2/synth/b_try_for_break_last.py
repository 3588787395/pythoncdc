# -*- coding: utf-8 -*-
def b_try_for_break_last(items):
    hit = 0
    try:
        for it in items:
            if not it:
                break
            hit += 1
    except BaseException:
        return -1
    return hit
