def test_method_before_break(data, key):
    result = []
    for item in data:
        if item == key:
            result.append(item)
            break
    else:
        result.append('not_found')
    return result
