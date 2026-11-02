def g5(it):
    first = last = None
    for x in it:
        yield (first, last, x)
