def g13(x, it):
    x
    first = last = next(it)
    for ip in it:
        yield (first, last, ip)
