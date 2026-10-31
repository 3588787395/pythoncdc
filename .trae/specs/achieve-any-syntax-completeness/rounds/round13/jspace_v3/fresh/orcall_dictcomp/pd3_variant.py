KEEP = 1
def g(**kw):
    return kw
def f(boundary, cls):
    r = g(etype=cls, boundary=boundary or KEEP)
    return r
