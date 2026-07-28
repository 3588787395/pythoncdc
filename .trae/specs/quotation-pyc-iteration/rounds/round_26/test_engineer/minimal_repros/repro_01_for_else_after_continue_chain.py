
def f(items, result):
    for key, value in items.items():
        if not key == 'skip':
            if key == 'a':
                continue
            else:
                result.append(value)
                continue
    else:
        result.append(-1)
