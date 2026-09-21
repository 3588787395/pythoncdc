# -*- coding: utf-8 -*-
"""R17-A 01 anchor：for + else 臂嵌套 if/else + 尾随赋值。

形状：for → `if A: 赋值 / else:` （嵌套 `if B and C: … else: …`）+ 两条尾随赋值，
链后还有一条循环体语句（外层 merge 的入口块）。
实测区域层：block=44 first_else=62 inner_merge=170 merge_=222 inloop=True term=False
⇒ 判据 ①②③⑤ 成立、④（旧）不成立。
实测判定：pre-patch MISMATCH（target_diff #13 JUMP 终点 orig=('text',LOAD_FAST)
decomp=('len',LOAD_GLOBAL)）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def normalize(rows, strict):
    for key, val in rows.items():
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
