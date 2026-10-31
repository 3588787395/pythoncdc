def f(pairs, opt):
    d = {a: b for a, b in pairs}
    d['n'] = len(d)
    return d['n'] if opt or d else 0
