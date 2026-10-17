# rec1_yf9_cond: Yield-F9 重建-核心单元：yield 表达式作 if 条件（3.11 括号必要形）
def f_yield_cond(xs):
    for i in range(3):
        if (yield i):
            yield i
    return
