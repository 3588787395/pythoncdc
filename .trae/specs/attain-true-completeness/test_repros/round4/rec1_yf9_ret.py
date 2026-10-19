# rec1_yf9_ret: Yield-F9 重建-核心单元：yield 表达式作 return 值（3.11 括号必要形）
def f_yield_ret(xs):
    for i in range(3):
        if i:
            return (yield i)
    return 0
