# -*- coding: utf-8 -*-
"""R13 负对照 D：try/except 里带 return（含 except 收尾），但 return 不在共享尾上。

对照 R13-E / R13-G / R13-H：这里每个 return 都在**唯一**前驱的分支里，
不存在 join 尾合并/条件丢失的歧义，尺子必须判 MATCH。
"""


def load(path, log, Order):
    try:
        data = open(path).read()
    except BaseException:
        log.error('read fail')
        return None
    rows = []
    for v in data:
        try:
            o = Order()
            o.save(v)
        except BaseException:
            log.error('parse fail')
            continue
        rows.append(o)
    return rows


def convert(x, log):
    if x is None:
        return 0
    if x < 0:
        log.error('neg')
        return -1
    return x * 2
