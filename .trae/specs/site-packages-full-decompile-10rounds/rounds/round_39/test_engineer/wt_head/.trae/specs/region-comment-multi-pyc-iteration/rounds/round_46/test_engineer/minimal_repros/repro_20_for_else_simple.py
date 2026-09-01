def func(items):
    result = {}
    for item in items:
        val = int(item)
        if val > 0:
            result[item] = val
        continue
    else:
        if result:
            return result
        raise ValueError("empty")
