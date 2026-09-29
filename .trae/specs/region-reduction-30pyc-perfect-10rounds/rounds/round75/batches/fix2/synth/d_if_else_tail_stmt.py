# -*- coding: utf-8 -*-
def d_if_else_tail_stmt(items, flag, log):
    if flag:
        return 1
    else:
        for it in items:
            if it:
                break
        del items
        log.append("x")
    return 0
