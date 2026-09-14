def f(data, exclude):
    try:
        for item in data:
            if item.startswith(exclude):
                continue
            processed = transform(item)
            return processed
        return None
        return None
    except BaseException:
        return 'error'

def transform(x):
    return x.upper()
