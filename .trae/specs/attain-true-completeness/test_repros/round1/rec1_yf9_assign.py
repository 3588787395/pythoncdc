# rec1_yf9_assign: Yield-F9 重建-对照单元：赋值位 yield（e12b f_yield_assign_rhs 同形）
def f_yield_assign(xs):
    for i in range(3):
        if i:
            v = yield i
            if v:
                yield v
    return
