def f(obj, pairs, opt):
    d = {a: b for a, b in pairs}
    o = obj
    o.x = len(d)
    return o.x if opt or d else 0
