def test():
    f = lambda x: (lambda y: x + y)
    g = f(5)
    return g(10)
