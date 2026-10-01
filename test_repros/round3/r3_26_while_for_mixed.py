"""r3_26: 深层嵌套 — while>for 混套（外层 while-else + 内层 for-else）。"""


def while_for_mixed(m, n):
    acc = []
    i = 0
    while i < m:
        for j in range(n):
            if (i * j) % 7 == 3:
                break
            acc.append((i, j))
        else:
            acc.append(("f-else", i))
        i += 1
        if i == 4:
            break
    else:
        acc.append("w-else")
    return acc


def while_for_continue_cross(m, n):
    """while 体 for-else 前后各一个 continue 路径。"""
    acc = []
    i = 0
    while i < m:
        i += 1
        if i % 2 == 0:
            continue
        for j in range(n):
            if j == i:
                continue
            if j > 5:
                break
            acc.append((i, j))
        else:
            if len(acc) > 9:
                continue
            acc.append(("fe", i))
    return acc


def nested_while_in_while_else(m, n):
    """while-else 体内再嵌 while（else 含循环子区域）。"""
    acc = []
    i = 0
    while i < m:
        if i == 2:
            break
        i += 1
    else:
        j = 0
        while j < n:
            if j % 2:
                acc.append(j)
            j += 1
        else:
            acc.append("inner-else")
    return acc
