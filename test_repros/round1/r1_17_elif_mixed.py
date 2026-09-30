# r1_17 elif 臂为混合链（if x: ... elif a and b or c: ...）
# 焦点：IF_ELIF_CHAIN × BoolOp 交叠


def f(a, b, c, x):
    total = 0
    if x:
        total += 1
    elif a and b or c:
        total += 4
    return total
