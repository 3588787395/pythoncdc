def f(items, opener):
    for x in items:
        if x:
            with opener(x) as h:
                h.read()
