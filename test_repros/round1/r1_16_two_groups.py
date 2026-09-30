# r1_16 两组无第三操作数（if a and b or c and d）
# 焦点：or 连接两个 and 组、无裸尾操作数


def f(a, b, c, d):
    total = 0
    if a and b or c and d:
        total += 4
    return total
