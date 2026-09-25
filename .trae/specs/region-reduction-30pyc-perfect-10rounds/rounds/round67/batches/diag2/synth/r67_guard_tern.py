def f(d, k, v):
    if not d or k not in d or len(d[k]) == 0:
        return v if k is None else v[k]
    acc = d[k]
    for i in range(len(acc)):
        acc = acc + i
    return acc
