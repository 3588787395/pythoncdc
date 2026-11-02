def g6(it, flag):
    first = last = flag or next(it)
    for x in it:
        yield (first, last, x)
