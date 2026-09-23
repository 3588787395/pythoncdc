def w(xs, g, h, k, c, out):
    for x in xs:
        if c:
            try:
                a = g(x)
            except Exception:
                h(x)
                return out
        else:
            k(x)
    return out
