# n1_02 负对照：浅层 or 链（当前算法应 MATCH）


def f(a, b):
    total = 0
    if a or b:
        total += 4
    return total
