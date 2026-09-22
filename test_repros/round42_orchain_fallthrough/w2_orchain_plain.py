def w2(a, b, c, acc):
    if not a or b not in c or len(c[b]) == 0:
        return -1
    t = acc
    for x in c[b]:
        t = t + x
    return t
