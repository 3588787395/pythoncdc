def h(addresses):
    it = iter(addresses)
    first = last = next(it)
    for ip in it:
        yield (first, last)
    yield (first, last)
