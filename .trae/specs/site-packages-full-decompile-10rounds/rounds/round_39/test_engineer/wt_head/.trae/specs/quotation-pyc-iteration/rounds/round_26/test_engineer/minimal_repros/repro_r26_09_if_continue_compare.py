
def f(items, out):
    for x in items:
        if x > 10:
            continue
        if x < 0:
            continue
        out.append(x)
