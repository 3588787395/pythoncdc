# -*- coding: utf-8 -*-
"""R13 负对照 A：普通 if/elif 链 + 循环 + return，不应触发任何 R13 缺陷。

用于证明 _r10_strict_check 这把尺子不会「见谁都报 MISMATCH」。
"""


def classify(scores, threshold, log):
    total = 0
    for name, value in scores:
        if value is None:
            continue
        if value > threshold:
            log.info(name)
            total += value
        elif value < 0:
            total -= 1
        else:
            total += 1
    return total


def pick(items, idx, table):
    for i in items:
        if i in table:
            return table[i]
    return None
