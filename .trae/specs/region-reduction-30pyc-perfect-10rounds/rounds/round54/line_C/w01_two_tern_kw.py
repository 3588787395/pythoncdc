def w(a, b, c, d, f):
    f(a, b, k1='p' if c else 'q', k2='r' if d else 's')
    return a
