def f(items, sub, g):
    for x in items:
        if x:
            g(x)
            for y in sub:
                if y:
                    break
