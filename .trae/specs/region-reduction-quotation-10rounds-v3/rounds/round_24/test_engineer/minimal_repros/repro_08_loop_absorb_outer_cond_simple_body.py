"""repro_08 — 缺陷2变体: while 循环体仅为单语句赋值（无内层 if/else）。

测试 while 循环体最简时，else 分支的 while 是否仍被 loop_else 吞噬。
"""
def f(flag, count):
    total = 0
    if flag == 0:
        while count > 0:
            total += count
            count -= 1
        if total > 10:
            start = str(total)
        else:
            start = '0' + str(total)
    elif count == 1:
        start = 'X'
    else:
        count -= 1
        while count > 0:
            total += count
            count -= 1
        if total > 10:
            start = str(total)
        else:
            start = '0' + str(total)
    return (start, total)
