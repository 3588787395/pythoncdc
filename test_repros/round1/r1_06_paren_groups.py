# r1_06 括号组 (a and b) or (c and d)
# 焦点：两个 and 组由 or 连接——BoolOpRegion op_chain 交替组


def f(a, b, c, d):
    total = 0
    if (a and b) or (c and d):
        total += 4
    return total
