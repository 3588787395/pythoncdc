KEEP = 1
def deco(**kw):
    return lambda c: c
def f(members, boundary, cls, name):
    vals = [t[0] for t in members]
    body = {t[0]: t[1] for t in members}
    body['__module__'] = 'm'
    tmp = type(name, (object,), body)
    cls = deco(etype=cls, boundary=boundary or KEEP)(tmp)
    return (cls, vals)
