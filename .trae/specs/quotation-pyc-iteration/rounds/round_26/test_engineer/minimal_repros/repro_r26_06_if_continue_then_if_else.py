
def f(items, out):
    for k, v in items.items():
        if k == 'skip':
            continue
        if k == 'a':
            out.append(v)
        else:
            out[k] = v
