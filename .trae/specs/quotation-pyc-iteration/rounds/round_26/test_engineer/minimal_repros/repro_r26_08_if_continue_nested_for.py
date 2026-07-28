
def f(data, out):
    for i in data:
        for key, value in i.items():
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
        out.append(1)
