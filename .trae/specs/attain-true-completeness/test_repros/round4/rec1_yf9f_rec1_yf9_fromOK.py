# Source Generated with Decompyle++ (Python version)
# File: rec1_yf9f_rec1_yf9_from.pyc (Python 3.11)

def f_yield_from_chain(xs):
    def inner():
        yield from xs
    for i in range(3):
        if i:
            yield from inner()
def f_yield_from_deep(xs):
    def lvl2():
        yield from xs
    def lvl1():
        for i in range(2):
            if i:
                yield from lvl2()
    for j in range(2):
        if j:
            yield from lvl1()
