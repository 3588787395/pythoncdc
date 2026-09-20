# -*- coding: utf-8 -*-
"""R14-10 复现：**关键字实参**里的两个同级推导式 `dump(a=[x for x in t], b=[y for y in u])`。

字节码与位置实参版只差一个键元组 LOAD_CONST + PRECALL/CALL 的 arg 形态，
仍然命中 chained-pair 探测器（尾部消费者 CALL 不在 `_expr_build` 白名单）。
实测缺陷指纹：`<module>.f [seq_len] orig=15 decomp=11`。
期望：MISMATCH（缺陷复现）。
"""


def dump(x):
    return x


def kwargs_two_comps(t, u):
    return dump(a=[x for x in t], b=[y for y in u])
