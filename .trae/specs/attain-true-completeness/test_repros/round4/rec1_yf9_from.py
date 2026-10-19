# rec1_yf9_from: Yield-F9 重建-对照单元：yield from 链（e12b f_yield_from_chain/f_yield_from_deep 同形）
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
