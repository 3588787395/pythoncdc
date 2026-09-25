# -*- coding: utf-8 -*-
"""R64 diag2 repro (c1 机制): 链式比较让位后，兄弟子区域入口块不得被吞。
真实缺陷 scheduler.pyc is_run_interval_time_now [225,201,2,173]；证据见 diag2/ANALYSIS.md。"""


def r64d2_chain_yield(t, A, B, C, D):
    if not t:
        return 0
    elif t:
        try:
            t = int(t)
        except BaseException:
            t = 0
        return (A < t < B) or (C < t < D)
    return 1
