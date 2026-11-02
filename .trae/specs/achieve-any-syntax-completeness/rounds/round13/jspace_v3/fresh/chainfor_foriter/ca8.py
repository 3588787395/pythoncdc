def g8(it):
    first = last = next(it)
    for x in it:
        print(x)
    return first
