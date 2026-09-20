# -*- coding: utf-8 -*-
"""R14-09 复现：**位置实参**里的两个同级推导式 `dump([x for x in t], [y for y in u])`。

与 dict 版同一根因，只是尾部消费者从 BUILD_CONST_KEY_MAP 换成 `CALL 2`。
`_expr_build` 白名单里没有任何 CALL 类操作码，因此「实参列表里的两个推导式」
同样被 chained-pair 探测器焊成一层嵌套：
  产物 `[y for y in [x for x in t]]`（dump 调用与第二个 iterable 一起消失）。
实测缺陷指纹：`<module>.f [seq_len] orig=14 decomp=11`。
期望：MISMATCH（缺陷复现）。
"""


def dump(x):
    return x


def call_args_two_comps(t, u):
    return dump([x for x in t], [y for y in u])
