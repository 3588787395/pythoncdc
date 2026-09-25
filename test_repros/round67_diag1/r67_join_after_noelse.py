def v1(a, b, c):
    r = []
    if a:
        if b:
            r = [1]
        else:
            r = [2]
    if c:
        return r
    return []


def v2(a, b, c):
    r = []
    if a:
        if b:
            r = [1]
        else:
            r = [2]
    if c is None:
        return r
    if isinstance(c, str):
        return [x for x in r if x == c]
    return []


def v3(obj, a, b, items, c):
    r = []
    if a:
        if b:
            for i in items:
                r.append(i)
            obj.all = r
        else:
            r = obj.all
    if c is None:
        return r
    if isinstance(c, str):
        return [x for x in r if x == c]
    return []


def v4(obj, a, b, items, c):
    r = []
    if a:
        if b:
            for i in items:
                r.append(i)
            obj.all = r
    if c is None:
        return r
    return []


def ok1(a, b):
    r = []
    if a:
        if b:
            r = [1]
        else:
            r = [2]
    return r
