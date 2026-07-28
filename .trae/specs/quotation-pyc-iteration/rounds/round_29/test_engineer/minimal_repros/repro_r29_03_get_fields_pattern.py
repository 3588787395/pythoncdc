def f(fans, fields):
    d = {1: 2, 3: 4}
    if fans == 1:
        d = d[1]
    elif fans == 2:
        d = d[2]
    elif fans == 3:
        d = d[3]
    elif fans in d.keys():
        d = d[fans]
        if not fields:
            return d
        else:
            return fields
    if fields is None:
        result = []
        for k in d:
            result.extend(d[k])
        return result
    return None
