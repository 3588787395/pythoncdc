# r1_08 if-elif-else 链内嵌 try/for/with
# 焦点：If 形态 × 异常/循环/上下文管理器组合的臂收集


def f(a, b, c, d, x):
    total = 0
    if a and b or c:
        try:
            total += 1
        except ValueError:
            total += 2
    elif x:
        for i in range(3):
            total += i
    else:
        with open('x.txt') as g:
            total += len(g.name)
    return total
