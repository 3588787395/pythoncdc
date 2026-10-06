def f(xs):
    r = 0
    for i in xs:
        if i:
            while i > 0:
                r = i
                i -= 1
    return r
