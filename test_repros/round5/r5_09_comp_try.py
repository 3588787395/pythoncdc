def t_try_wrap(xs):
    try:
        return [x * 2 for x in xs]
    except TypeError:
        return []


def t_try_in_loop(xs):
    out = []
    for x in xs:
        try:
            out.append(x / (x - 2))
        except ZeroDivisionError:
            out.append([x] * 2)
    return out


def t_attr_chain(objs):
    return [o.get('k', 0) + o.id for o in objs]


def t_subscript(d, keys):
    return [d[k] + d.get(k, 1) for k in keys]


def t_method_chain(raw):
    return [s.strip().lower().split(',')[0] for s in raw]


def t_try_finally(xs):
    log = []
    try:
        return [x for x in xs]
    finally:
        log.append(len(xs))
