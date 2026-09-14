def for_if_no_else_with_continue(items):
    result = []
    for item in items:
        if item < 0:
            continue
        result.append(item)
    return result
