def yp1(items, enc):
    def inner(lst):
        yield 'HEAD'
        if not lst:
            return None
        yield enc(lst)
        yield 'TAIL'
    return inner
