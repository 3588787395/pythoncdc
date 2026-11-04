def p(a, b, c, f):
    if a or (b and c):
        f.v = 1
    return f
