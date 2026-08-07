def for_continue(items):
    result = []
    for item in items:
        if item < 0:
            continue
        result.append(item)
    return result
