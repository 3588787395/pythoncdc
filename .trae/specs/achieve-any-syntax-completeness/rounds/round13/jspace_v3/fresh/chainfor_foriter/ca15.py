def g15(it, k):
    first = last = next(it) if k else None
    for x in it:
        yield (first, last, x)
