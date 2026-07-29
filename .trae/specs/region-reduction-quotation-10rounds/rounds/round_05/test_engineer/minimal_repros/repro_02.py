"""repro_02: 复现 fill_minute_or_day_blank 同类缺陷（ternary merge block 多重赋值）。

缺陷模式：`result = val1 if cond else val2; a = x; b = y; c = func(a, b); if c > 0: ...`
三元 STORE_* 之后的多条独立赋值（a=, b=, c=）被整体跳过。

根因：与 repro_01 相同 —— _cond_block_is_ternary_merge 标志在首个 STORE_* 后未清除，
覆盖 cond_block 内全部 STORE_*。
"""


def f(cond, val1, val2, x, y):
    result = val1 if cond else val2
    a = x
    b = y
    c = a + b
    if c > 0:
        return result
    return c
