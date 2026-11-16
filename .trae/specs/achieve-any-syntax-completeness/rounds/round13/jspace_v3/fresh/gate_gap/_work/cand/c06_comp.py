def _host():
    pass

def outer(ns):
    a = [x * 2 for x in ns if x > 0]
    b = {k: v for k, v in zip(ns, ns)}
    c = {x + 1 for x in ns}
    d = (y - 1 for y in ns)
    return a, b, c, d
