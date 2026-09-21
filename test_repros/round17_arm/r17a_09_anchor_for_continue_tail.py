# -*- coding: utf-8 -*-
"""R17-A 09 anchor：尾随语句含 **continue**。

形状：for → if/else（else 臂 = 嵌套 if/elif/else + 尾随 `if n == 0: continue` + 尾随赋值），
链后是 `report.append((key, n))`。continue 在 3.11 里跳向 FOR_ITER 回边重检块，
与 break 的落点不同。
实测：block=44 first_else=62 inner_merge=96 merge_=146 inloop=True term=False；
pre-patch MISMATCH（target_diff #13）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def refresh(rows, limit, report):
    for key, val in rows.items():
        if val is None:
            n = 0
        else:
            if val > limit:
                n = limit
            elif val < 0:
                n = 0
            if n == 0:
                continue
            n = n + len(key)
        report.append((key, n))
    return report
