# r1_01 语句上下文混合 and/or 链（B1b 归档形态：if a and b or c）
# 焦点：BoolOp 破口族 B1 —— 语句上下文 or 臂第二丢弃入口


def f(a, b, c):
    total = 0
    if a and b or c:
        total += 4
    return total
