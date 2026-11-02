def g4(it):
    a = b = c = next(it)
    for x in it:
        yield (a, b, c, x)
