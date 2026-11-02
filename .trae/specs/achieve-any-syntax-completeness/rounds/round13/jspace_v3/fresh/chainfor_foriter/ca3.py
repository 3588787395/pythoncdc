def k(it):
    first = last = next(it)
    for ip in it:
        if ip != last:
            yield (first, last)
            first = ip
        last = ip
