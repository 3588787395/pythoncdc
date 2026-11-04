def p(a, b, c, f):
    if a or (b and c):
        raise TypeError('x')
    return f
