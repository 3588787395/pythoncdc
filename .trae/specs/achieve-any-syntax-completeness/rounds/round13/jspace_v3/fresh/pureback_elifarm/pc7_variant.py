def f(a, b):
    t1 = None
    for x in a:
        if x is None:
            continue
        elif x > 1:
            t1 = x
            break
    t2 = None
    for y in b:
        if y is None:
            continue
        elif y > 1:
            t2 = y
            break
    return (t1, t2)
