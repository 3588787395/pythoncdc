
def f(items, out):
    for k, v in items.items():
        if not k == 'skip':
            if k == 'x':
                continue
            else:
                out[k] = v
                continue
    else:
        out.append(0)
