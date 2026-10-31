KEEP = 1
def decorate(**kw):
    return lambda c: c
def f(boundary, cls, tmp_cls):
    cls = decorate(etype=cls, boundary=boundary or KEEP)(tmp_cls)
    return cls
