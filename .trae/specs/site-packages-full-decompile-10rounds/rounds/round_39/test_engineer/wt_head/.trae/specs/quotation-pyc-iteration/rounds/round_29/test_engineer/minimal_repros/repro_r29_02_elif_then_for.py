def f(x, d):
    if x == 1:
        d = d[1]
    elif x == 2:
        d = d[2]
    elif x == 3:
        d = d[3]
    result = []
    for k in d:
        result.extend(d[k])
    return result
