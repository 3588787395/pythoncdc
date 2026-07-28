
def f(items, out):
    while items:
        x = items.pop()
        if x == 0:
            continue
        if x == 1:
            continue
        out.append(x)
