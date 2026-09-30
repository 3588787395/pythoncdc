# r1_03 ≥3 层混合链（if a and b or c and d or e）
# 焦点：三层交替 and/or，链内两个 and 组


def f(a, b, c, d, e):
    total = 0
    if a and b or c and d or e:
        total += 4
    return total
