
def func(items):
    result = []
    for item in items:
        try:
            result.append(item * 2)
        except TypeError:
            result.append(0)
    return result
