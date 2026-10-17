# rec1_yf9_boolop: Yield-F9 重建-核心单元：yield 表达式作 boolop 操作数（e12f 同形最小化）
def f_yield_boolop(xs):
    for i in range(3):
        if i:
            yield (yield i) or 0
    return
