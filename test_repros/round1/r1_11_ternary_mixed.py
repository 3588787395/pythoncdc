# r1_11 三元表达式上下文混合链（x = 1 if a and b or c else 2）
# 焦点：TERNARY × BoolOp 的表达式上下文消费


def f(a, b, c):
    x = 1 if a and b or c else 2
    return x
