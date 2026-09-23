def w(a, b, c, d, f):
    f(a, 'p' if c else 'q', b, 'r' if d else 's')
    return a
