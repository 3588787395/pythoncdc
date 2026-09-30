# r1_20 括号 or 组前导 + and（if (a or b) and c）
# 焦点：or 组作为 and 链首（op_chain 交替方向）


def f(a, b, c):
    total = 0
    if (a or b) and c:
        total += 4
    return total
