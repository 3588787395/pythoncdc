def w(it, g, h):
    while it:
        try:
            a = g(it)
        except Exception:
            h(it)
