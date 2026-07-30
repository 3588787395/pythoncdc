"""repro_07 — 缺陷2变体: if/elif/else，then 与 else 均含 while+if/else，elif 简单。

elif 简单分支是触发 loop_else 吞噬的关键（对照 repro_05）。
"""
def f(flag, count):
    month = 5
    year = 2020
    if flag == 0:
        while count > 0:
            if month - count <= 0:
                year -= 1
                count -= month
                month = 12
            else:
                month = month - count
                count = 0
        if month in (10, 11, 12):
            start = str(year) + str(month)
        else:
            start = str(year) + '0' + str(month)
    elif count == 1:
        start = 'Y'
    else:
        count -= 1
        while count > 0:
            if month - count <= 0:
                year -= 1
                count -= month
                month = 12
            else:
                month = month - count
                count = 0
        if month in (10, 11, 12):
            start = str(year) + str(month)
        else:
            start = str(year) + '0' + str(month)
    return (start, year)
