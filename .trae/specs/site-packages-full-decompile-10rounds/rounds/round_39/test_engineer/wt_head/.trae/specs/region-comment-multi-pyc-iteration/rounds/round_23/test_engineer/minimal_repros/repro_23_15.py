def nested_for_cond(data, keys):
    result = {}
    for key in keys:
        if key in data:
            val = data[key]
            if isinstance(val, list):
                result[key] = val[0]
            else:
                result[key] = val
    return result
