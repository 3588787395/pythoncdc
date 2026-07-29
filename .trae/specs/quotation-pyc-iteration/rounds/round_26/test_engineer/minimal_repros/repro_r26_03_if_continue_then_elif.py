
def f(items, out):
    for k, v in items.items():
        if k == 'skip':
            continue
        if k == 'x':
            continue
        elif isinstance(v, dict):
            out.update(v)
            continue
        else:
            out[k] = v
            continue
