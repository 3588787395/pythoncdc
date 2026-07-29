
def f(items, out):
    for x in items:
        if x == 1:
            continue
        elif x == 2:
            out.append(x)
            continue
        else:
            out.append(x * 2)
            continue
    else:
        out.append(-1)
