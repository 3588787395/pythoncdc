# -*- coding: utf-8 -*-
"""R17-A 18 anchor：**双层 for** 的内层循环里 + and-BoolOp 条件。

形状：for → for → if/else（else 臂 = 嵌套 `if flag_c and isinstance(...)` / else
+ 两条尾随赋值），链后是 `report.append((row, col, n))`。
 enclosing loop 取最近的一层（内层 for），删④后同样被正确否决。
实测：block=74 first_else=92 inner_merge=174 merge_=184 inloop=True term=False；
pre-patch MISMATCH（target_diff #21 orig=('report',LOAD_FAST)
decomp=('n',LOAD_FAST)）→ post-patch MATCH。角色：锚点（SENTINEL）。"""


def collect(matrix, report, flag_c):
    for row, cells in enumerate(matrix):
        for col, val in enumerate(cells):
            if val is None:
                n = 0
            else:
                if flag_c and isinstance(val, int):
                    n = val
                else:
                    n = int(val)
                n = n + col
            report.append((row, col, n))
    return report
