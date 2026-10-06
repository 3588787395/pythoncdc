def b2a02_shallow(items, limit):
    out = []
    for it in items:
        if it > limit:
            continue
        out.append(it)
    return out


def b2a02_deep(items, limit):
    out = []
    while limit > 0:
        try:
            for it in items:
                if it > 0:
                    if it > limit:
                        continue
                    out.append(it)
        except ValueError:
            limit = 0
        limit -= 1
    return out
