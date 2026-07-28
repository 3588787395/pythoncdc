
def f(items, out):
    for k, v in items.items():
        if k == 'a':
            continue
        elif isinstance(v, dict):
            out.update(v)
            continue
        else:
            out[k] = v
            continue
    else:
        out.append(0)
