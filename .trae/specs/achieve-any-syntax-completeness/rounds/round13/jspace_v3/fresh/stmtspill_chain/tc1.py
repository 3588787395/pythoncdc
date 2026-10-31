def f(o, c1, c2, v1, v2):
    o.x = v1 if c1 else v1
    o.y = v2 if c2 else v2
    return o
