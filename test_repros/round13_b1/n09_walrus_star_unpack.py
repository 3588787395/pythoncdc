def w(data, obj):
    if (n := len(data)) > 3: pass
    a, *b = data
    (c, d) = data; [e, f] = data
    s = {*data, *data}; t = [*data, *data]; dd = {**data, **data}
    obj.x += (a and b)
    obj[0] += (a or b)
    p = q = r = n            # COPY 链
    lst = [0]; lst[0], a = 1, 2
