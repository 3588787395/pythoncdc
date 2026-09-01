
def f(items, out):
    for x in items:
        if isinstance(x, str):
            continue
        if isinstance(x, dict):
            continue
        out.append(x)
