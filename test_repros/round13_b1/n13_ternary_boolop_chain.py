def tb(a, b, c):
    x = a if (b and c) else (c if b else a)
    y = (a or b) if (b or c) else (a and c)
    z = 1 if a < b < c else 2
    w = x if y else z if x else y
    v = (a and b) or (c and x) or (b and y)
    u = x if (a or b or c) else y if a else z
    return v if u else w
