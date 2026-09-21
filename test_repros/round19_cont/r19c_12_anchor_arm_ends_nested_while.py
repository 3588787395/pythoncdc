def f(items, n, g):
    for x in items:
        if x:
            while n > 0:
                n -= 1
                g(n)
