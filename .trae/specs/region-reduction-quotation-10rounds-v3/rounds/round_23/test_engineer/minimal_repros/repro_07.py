"""repro_07: if-continue 兄弟语句 — 嵌套 if 后跟 continue（无 break 路径）。

测试 aspect: 外层 if 无 else（无 break 路径），仅 if-continue 兄弟结构。
循环体只有 if + continue 兄弟，无 post-loop 块。验证最简 if-continue 兄弟模式。

    for j in range(n):
        if outer_cond:
            if inner_cond:
                x = 1
            continue
"""


def f(data):
    total = 0
    for j in range(len(data)):
        if data[j] > 0:
            if data[j] > 10:
                total += data[j]
            continue
        total -= 1
    return total
