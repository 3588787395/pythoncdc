def for_try_continue(items):
    result = []
    for item in items:
        try:
            val = int(item)
        except:
            continue
        result.append(val)
    return result
