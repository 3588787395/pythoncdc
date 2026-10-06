def r_d1(a, b, c, d):
    return ((a or b) and c) or d


def r_d2(a, b, c, d):
    return a and ((b or c) and d)


def r_e3(a, b, c, d):
    return a or (b and (c or d))


def r_g2(a, b, c, d, e):
    return (a and (b or c)) or (d and e)
