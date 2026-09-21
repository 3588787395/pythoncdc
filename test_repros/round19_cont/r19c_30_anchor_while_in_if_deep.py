def f(items, n, g, h):
    for x in items:
        if x:
            if n:
                h(n)
            while n > 0:
                n -= 1
                g(n)
