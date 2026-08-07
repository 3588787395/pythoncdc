def for_after_if_return(items, check):
    if len(items) == 0:
        return items
    result = []
    for item in items:
        if item == check:
            result.append(item)
    return result
