# -*- coding: utf-8 -*-
def e_while_tail(items, log):
    hit = 0
    while items:
        it = items.pop()
        if it < 0:
            break
        hit += it
    del items
    log.append(hit)
    return hit
