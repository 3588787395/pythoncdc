def w(xs, g, h, k):
    for x in xs:
        try:
            a = g(x)
        except Exception:
            h(x)
        else:
            k(x)
