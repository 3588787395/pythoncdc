"""repro_06: if-continue 兄弟语句 — 内层 if 条件为复合比较。

测试 aspect: 内层 if 条件为复合比较（j == len(x) - 1），与 get_str_data 的
实际条件一致。验证复合比较条件不影响 continue 兄弟发射。

    for j in range(n):
        if outer_cond:
            if j == len(items) - 1:
                x = 1
            continue
        y = j
        break
"""


def f(items):
    found = -1
    for j in range(len(items)):
        if items[j] > 0:
            if j == len(items) - 1:
                found = j
            continue
        found = -j
        break
    return found
