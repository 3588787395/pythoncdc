def g14(it):
    total = 0
    first = last = next(it)
    for x in it:
        total += 1
    return first + last + total
