# r1_02 语句上下文 or 先行混合链（if a or b and c）
# 焦点：or 链首 + and 次组的语句上下文消费


def f(a, b, c):
    total = 0
    if a or b and c:
        total += 4
    return total
