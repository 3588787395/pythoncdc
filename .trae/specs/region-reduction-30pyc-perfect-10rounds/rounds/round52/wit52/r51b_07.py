
def f(xs):
    n = 0
    for x in xs:
        if x == 1:
            n += 1
        elif x == 2:
            n += 2
        else:
            pass
        n += x
    return n
