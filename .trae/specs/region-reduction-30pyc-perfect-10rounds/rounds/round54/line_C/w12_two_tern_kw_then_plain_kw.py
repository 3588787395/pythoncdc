def w(a, b, c, d, f):
    f(a, k1='p' if c else 'q', k2='r' if d else 's', k3=b)
    return a
