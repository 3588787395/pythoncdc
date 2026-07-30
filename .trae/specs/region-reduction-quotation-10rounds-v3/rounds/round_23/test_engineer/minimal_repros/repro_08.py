"""repro_08: if-continue 兄弟语句 — STORE_FAST 赋值作为 true 分支语句。

测试 aspect: 内层 if true 分支为 STORE_FAST 赋值（data_is_nan = 1），与
get_str_data 完全一致。验证 STORE_FAST 赋值 + continue 兄弟的发射顺序。

    for j in range(n):
        if flags[j]:
            if j == n - 1:
                data_is_nan = 1
            continue
        not_nan = j
        break
"""


def f(flags):
    data_is_nan = 0
    not_nan = 0
    n = len(flags)
    for j in range(n):
        if flags[j]:
            if j == n - 1:
                data_is_nan = 1
            continue
        not_nan = j
        break
    return (data_is_nan, not_nan)
