"""repro_05: if-continue 兄弟语句 — 外层 if 有 else（break 路径）。

测试 aspect: 外层 if 的 false 分支跳到 post-loop 块（break 语义），内层 if 的
两分支均→回边（continue 兄弟）。验证外层 if-else + 内层 if-continue 兄弟
共存的复合结构。

本 repro 最接近 get_str_data 的实际形态：
    for j in range(len(is_all_nan)):
        if is_all_nan[j] == True:       # 外层 if
            if j == len(is_all_nan) - 1:  # 内层 if
                data_is_nan = 1
            continue                      # ← 兄弟语句
        not_nan_icount = j                # else 分支
        break
"""


def f(flags):
    last = -1
    for j in range(len(flags)):
        if flags[j] == True:
            if j == len(flags) - 1:
                last = j
            continue
        last = j
        break
    return last
