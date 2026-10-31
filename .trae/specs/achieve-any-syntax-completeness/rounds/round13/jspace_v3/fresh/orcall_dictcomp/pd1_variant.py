KEEP = 1
def decorate(**kw):
    return lambda c: c
def f(members, boundary, cls, name):
    body = {t[0]: t[1] for t in members}
    body['__module__'] = 'm'
    tmp_cls = type(name, (object,), body)
    cls = decorate(etype=cls, boundary=boundary or KEEP)(tmp_cls)
    return cls
