def f(a, d, s):
    if a:
        d = 1
    elif d:
        d = d.strip()
        if d in s:
            d = ''
    return d
