
def f(items, out):
    for key, value in items.items():
        if key == 'skip':
            continue
        if key == 'a':
            continue
        elif isinstance(value, dict):
            out.update(value)
            continue
        else:
            out[key] = value
            continue
    out.append(0)
