def f(xs):
    r = 0
    for i in xs:
        while i > 0:
            i -= 1
            r += i
    return r
