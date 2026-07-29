
def f(items, out):
    for x in items:
        if x > 0:
            if x == 5:
                continue
            else:
                out.append(x)
                continue
    else:
        out.append(-1)
