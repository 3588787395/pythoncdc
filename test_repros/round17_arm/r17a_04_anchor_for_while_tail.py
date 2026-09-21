# -*- coding: utf-8 -*-
"""R17-A 04 anchor：尾随语句是 **while 循环**。

形状：for → if/else（else 臂 = 嵌套 if/else + 尾随 while + 尾随 append），
链后是 `report.append(...)`（外层 merge 首指令 LOAD_FAST report）。
实测：block=44 first_else=62 inner_merge=166 merge_=242 inloop=True term=False；
pre-patch MISMATCH（target_diff #13 orig=('report',LOAD_FAST) decomp=('n',LOAD_FAST)）
→ post-patch MATCH。角色：锚点（SENTINEL）。
注：与 27 号（同形状但 merge 首指令与尾随首指令同为 LOAD_FAST n）对照，
可见「尺子能否看见」只取决于两个终点的指令签名是否不同。"""


def clamp(values, limit, clamped, report):
    for name, raw in values.items():
        if raw is None:
            n = 0
        else:
            if isinstance(raw, int):
                n = raw
            else:
                n = int(float(raw))
            while n > limit:
                n = n // 2
            clamped.append(name)
        report.append((name, n))
    return values
