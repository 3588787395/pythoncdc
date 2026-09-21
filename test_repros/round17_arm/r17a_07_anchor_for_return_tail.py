# -*- coding: utf-8 -*-
"""R17-A 07 anchor：尾随语句是 **提前 return 守卫**（`if …: return`）。

形状：for → if/elif/else（else 臂 = 嵌套 if/else + 尾随 `if n < 0: return None`），
链后是 `report.append(...)`。外层链有三臂，故 `_build_elif_region` 被递归调用多次
（实测 3 次命中守卫，其中一次 inner_merge==merge_ 走 ③ 放行）。
实测：block=62 first_else=80 inner_merge=158 merge_=176 inloop=True term=False；
pre-patch MISMATCH（target_diff #13）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def validate(rows, limit, report):
    for key, val in rows.items():
        if val is None:
            n = 0
        elif val > limit:
            n = limit
        else:
            if isinstance(val, int):
                n = val
            else:
                n = int(val)
            if n < 0:
                return None
        report.append((key, n))
    return report
