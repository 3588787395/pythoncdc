def w3(a, b, c, d):
    if not c or a not in c or len(c[a]) == 0 or b == d:
        return 0
    return c[a]
