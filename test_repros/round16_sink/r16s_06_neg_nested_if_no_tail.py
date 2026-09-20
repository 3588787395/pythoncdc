# -*- coding: utf-8 -*-
"""R16-S 06 neg nested if no tail
r16s_04 的 else 臂只留嵌套 if/else，**删掉尾随语句**（`side = val.w; out = out + side`）。
此时嵌套 if 的归并点 == 外层归并点（inner_merge is merge_），D2 判据③不成立。

真实目标：证明「尾随语句」是必要成分——没有尾随语句时展平成 elif 链是**正确**的
（CPython 对 `if A: .. else: if C: .. else: ..` 与 `if A: .. elif ... else:` 生成同一 CFG）。
"""


def classify(items, flag_a, flag_c, flag_d):
    for name, val in items:
        if flag_a:
            out = 1
        else:
            if flag_c:
                out = val.x
            else:
                out = val.z
        items[name] = out
    return items
