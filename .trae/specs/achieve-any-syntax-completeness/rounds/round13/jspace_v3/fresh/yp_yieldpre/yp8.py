def yp8(lst, enc):
    yield 'S'
    if not lst:
        return None
    for x in lst:
        yield enc(x)
    yield 'E'
    if not lst:
        del lst[:]
    return None
