# -*- coding: utf-8 -*-
"""R17-A 16 anchor：**外层 or 短路条件** + 尾随增量赋值。

形状：for → `if armed or val > limit:` / else（嵌套 if/else + `out += len(rows)`），
链后是 `report.append((name, out))`。or 的短路归并块与 if 的 else 入口共用，
是 elif 归并最容易误吞的场景。
实测：block=44 first_else=74 inner_merge=152 merge_=188 inloop=True term=False；
pre-patch MISMATCH（target_diff #17 orig=('report',LOAD_FAST)
decomp=('out',LOAD_FAST)）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def settle(rows, report, armed, limit):
    for name, val in rows.items():
        if armed or val > limit:
            out = limit
        else:
            if isinstance(val, float):
                out = int(val)
            else:
                out = val
            out += len(rows)
        report.append((name, out))
    return report
