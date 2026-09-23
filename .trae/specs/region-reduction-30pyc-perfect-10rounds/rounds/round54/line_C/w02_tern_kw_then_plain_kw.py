def w(a, b, c, f):
    f(a, k1='p' if c else 'q', k2=b)
    return a
