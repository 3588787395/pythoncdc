"""repro_06 — 缺陷2变体: if/elif/else，仅 else 分支含 while+if/else。

最小化 else 分支的 while 被 loop_else 吞噬的场景。
"""
def f(flag, count):
    month = 5
    year = 2020
    if flag == 0:
        start = 'A'
    elif count == 1:
        start = 'B'
    else:
        count -= 1
        while count > 0:
            if month - count <= 0:
                year -= 1
                month = 12
            else:
                month = month - count
                count = 0
        if month in (10, 11, 12):
            start = str(year) + str(month)
        else:
            start = str(year) + '0' + str(month)
    return (start, year)
