def g7(it, xs):
    first = last = next(it)
    for x in xs:
        yield (first, last, x)
