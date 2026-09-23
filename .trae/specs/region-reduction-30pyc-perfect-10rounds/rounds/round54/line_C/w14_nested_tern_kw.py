def w(a, b, c, d, f):
    f(a, k1=a if c else (b if d else c), k2=b)
    return a
