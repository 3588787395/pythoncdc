def for_else_with_continue(data):
    result = 0
    for item in data:
        if item > 0:
            result += item
        continue
    else:
        result = -1
    return result
