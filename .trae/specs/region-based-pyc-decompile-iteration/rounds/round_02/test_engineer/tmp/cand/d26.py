def f(items, bad):
    out = []
    for i in items:
        if i not in bad:
            out.append(i)
    return out
