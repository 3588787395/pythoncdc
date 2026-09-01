
def f(items, out):
    for x in items:
        if x == 0:
            continue
        out.append(x)
    else:
        out.append(-1)
