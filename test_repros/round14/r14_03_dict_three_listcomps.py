# -*- coding: utf-8 -*-
"""R14-03 边界：dict 字面量里**三个**同级推导式（兄弟数 = 3）。

实测（本机 3.11.7，PYTHONHASHSEED=0）：该形状 **不复现** ——
产物为 `{'a': [x for x in t], 'b': [y for y in u], 'c': [z for z in v]}`，
`<module>.f` 严格一致（MATCH）。
含义：焊接只发生在「恰好一对相邻 MAKE_FUNCTION」上，
即 `comprehension_generator.py:111-144` 的 chained-pair 探测器是**成对**消费的，
三个兄弟时该分支整体放弃（return None），走通用栈重建路径 → 正确。
期望：UNCONFIRMED（该形状未复现缺陷；实测应为 MATCH，一旦变成 MISMATCH
说明修复把「成对」判据改成了「连续段」判据，需回查）。
"""


def three_comps(t, u, v):
    return {'a': [x for x in t], 'b': [y for y in u], 'c': [z for z in v]}
