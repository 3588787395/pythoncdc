def f(pairs, opt):
    d = {a: b for a, b in pairs}
    d['a'] = len(d)
    d['b'] = opt
    return d['a'] if opt or d else 0
