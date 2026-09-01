def f(x, d):
    if x == 1:
        d = d[1]
    elif x == 2:
        d = d[2]
    elif x in d:
        return d[x]
    result = []
    for k in d:
        result.append(k)
    return result
