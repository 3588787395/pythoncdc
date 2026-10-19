# rec1_yf9_prec: Yield-F9 重建-可编译性对照：yield 表达式作 binop 左操作数（优先级面）
def f_yield_binop(xs):
    for i in range(3):
        if i:
            v = (yield i) + 1
            yield v
    return
