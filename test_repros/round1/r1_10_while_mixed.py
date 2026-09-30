# r1_10 while 条件为混合链（while a and b or c）
# 焦点：循环条件上下文的 BoolOp 消费（非 if 语句上下文）


def f(a, b, c):
    total = 0
    n = 0
    while a and b or c:
        total += 1
        n += 1
        if n > 9:
            break
    return total
