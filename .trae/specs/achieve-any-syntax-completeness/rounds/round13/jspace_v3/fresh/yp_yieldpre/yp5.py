def yp5(items, enc):
    def inner(lst):
        first = True
        for x in lst:
            if first:
                first = False
            else:
                yield '|'
            yield enc(x)
        yield 'END'
        if first:
            return None
        else:
            return None
    return inner
