"""r3_24: 双层循环 break 内外层 — 内层 break / 外层 break / 双层 else。"""


def double_loop_inner_break(m, n):
    acc = []
    for i in range(m):
        for j in range(n):
            if j == 2:
                break
            acc.append((i, j))
        else:
            acc.append(("else", i))
    return acc


def double_loop_outer_break(m, n):
    """外层 break（内层 for-else 正常耗尽后触发）。"""
    acc = []
    for i in range(m):
        for j in range(n):
            if i + j > 6:
                break
        else:
            if i == 3:
                break
            acc.append(i)
    return acc


def double_loop_both_else(m, n):
    acc = []
    i = 0
    while i < m:
        j = 0
        while j < n:
            if (i * j) % 5 == 4:
                break
            j += 1
        else:
            acc.append(("inner", i, j))
        i += 1
    else:
        acc.append("outer")
    return acc


def double_break_with_continue(m, n):
    """内层 continue 与外层 break 混排。"""
    acc = []
    for i in range(m):
        if i == 0:
            continue
        for j in range(n):
            if j == 0:
                continue
            if i * j > 9:
                break
            acc.append(i * j)
        else:
            acc.append(-1)
    return acc
