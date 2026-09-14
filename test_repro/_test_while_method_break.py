def while_method_break(data, key):
    result = []
    i = 0
    while i < len(data):
        if data[i] == key:
            result.append(data[i])
            break
        i += 1
    else:
        result.append('not_found')
    return result
