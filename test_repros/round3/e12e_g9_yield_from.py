# e12e: e12 拆分补测——yield 赋值右值 / yield from 链（发射文本合法，取单元读数）
def f_yield_assign_rhs(xs):
    for i in range(3):
        if i:
            v = yield i
            if v:
                yield v
    return


def f_yield_from_chain(xs):
    def inner():
        yield from xs
    for i in range(3):
        if i:
            yield from inner()
    return


def f_yield_from_deep(xs):
    def lvl2():
        yield from xs
        return

    def lvl1():
        for i in range(2):
            if i:
                yield from lvl2()
    for j in range(2):
        if j:
            yield from lvl1()
    return
