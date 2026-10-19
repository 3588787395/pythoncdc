# rec1_yf9_arg: Yield-F9 重建-核心单元：yield 表达式作调用实参（e12c 同形最小化）
def f_yield_arg(xs):
    def sink(x):
        return x
    for i in range(3):
        if i:
            yield sink((yield i))
    return
