
def f(items, out):
    for k, v in items.items():
        if not k == 'skip':
            out[k] = v
            continue
    else:
        out.append(0)
