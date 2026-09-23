def w(xs, g, h):
    n = 0
    for x in xs:
        try:
            a = g(x)
        except Exception:
            h(x)
        n = n + 1
    return n
