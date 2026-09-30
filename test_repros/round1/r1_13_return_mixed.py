# r1_13 return 表达式上下文混合链（return a and b or c）
# 焦点：表达式上下文（非语句丢弃路径）的 BoolOp 消费


def f(a, b, c):
    return a and b or c
