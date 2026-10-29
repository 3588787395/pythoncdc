def f(items):
    result = []
    while True:
        if not items:
            return result
        result.append(items[0])
        items = items[1:]
