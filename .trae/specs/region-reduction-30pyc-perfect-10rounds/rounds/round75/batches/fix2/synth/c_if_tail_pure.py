# -*- coding: utf-8 -*-
def c_if_tail_pure(items, flag):
    if flag:
        for it in items:
            if it:
                break
    return None
