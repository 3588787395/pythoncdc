def test(items=[]):
    result = []
    for item in items:
        if item > 0:
            result.append(item)
    return result
