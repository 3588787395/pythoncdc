# -*- coding: utf-8 -*-
"""R17-A 24 负对照：**没有任何循环**包裹的同一形状。

形状：函数体内顺序语句 → if/else（else 臂 = 嵌套 if/else + 两条尾随赋值），链后一条赋值。
实测：block=0 first_else=58 inner_merge=166 merge_=218 inloop=**False** term=False
⇒ 判据④在旧核上成立、在新核上被删除，两种情况下 D2 守卫都否决 → 行为逐字相同，
实测两世界均 MATCH。角色：负对照（删④不影响非循环场景）。"""


def normalize(rows, strict):
    key = 'a'
    val = rows.get('a')
    if val is None:
        text = ''
    else:
        if strict and isinstance(val, str):
            text = repr(val)
        else:
            text = str(val)
        pad = len(text) % 4
        text = text + ' ' * pad
    rows[key] = text
    return rows
