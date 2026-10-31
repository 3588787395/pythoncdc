def yp6(items, enc):
    def inner(lst):
        out = 0
        for x in lst:
            if (yield enc(x)):
                out += 1
        return out
    return inner
