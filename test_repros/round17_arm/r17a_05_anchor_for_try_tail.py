# -*- coding: utf-8 -*-
"""R17-A 05 anchor：尾随语句是 **try/except**。

形状：for → if/else（else 臂 = 嵌套 if/else + 尾随 try/except + 尾随 append）。
Round 16 的同类形状（r16s_13）落在尺子盲区；本例把链后的外层 merge 换成
`report.append(...)`，使两个终点签名不同，于是同一展平变得可测。
实测：block=44 first_else=62 inner_merge=140 merge_=258 inloop=True term=False；
pre-patch MISMATCH（target_diff #13 orig=('report',LOAD_FAST) decomp=('n',LOAD_FAST)）
→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def coerce(rows, offset, report):
    for key, raw in rows.items():
        if raw is None:
            n = 0
        else:
            if isinstance(raw, int):
                n = raw
            else:
                n = int(raw)
            try:
                n = n + len(offset)
            except TypeError:
                n = 0
            offset.append(key)
        report.append((key, n))
    return rows
