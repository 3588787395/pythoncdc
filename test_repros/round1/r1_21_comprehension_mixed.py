# r1_21 推导式筛选子句中的混合链
# 焦点：comprehension 管线 × BoolOp（专用管线交界）


def f(a, b, c):
    return len([1 for _ in range(3) if a and b or c])
