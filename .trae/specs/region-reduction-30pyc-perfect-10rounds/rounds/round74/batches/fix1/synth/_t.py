
def f(a, xs, n):
    d = {}
    if a and n > 0:
        if n == 1:
            d = g(n)
            if not d:
                return d
        else:
            for x in xs:
                if not x:
                    continue
                d[x] = x
                continue
        return d
    d = g(n)
    return d
