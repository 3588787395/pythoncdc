def f(o, d, opt):
    o['x'] = 1 if opt else 2
    return o['y'] if opt or d else 0
