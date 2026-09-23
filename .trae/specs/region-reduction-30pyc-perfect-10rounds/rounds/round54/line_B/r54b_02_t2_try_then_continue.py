def w(xs, g, h):
    for x in xs:
        try:
            a = g(x)
        except Exception:
            h(x)
        continue
