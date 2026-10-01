# r2_06 循环内 try+continue（R76-D 族相关）
# 焦点：try 体/handler 内 continue 的continue-sink 交互


def f(items, key):
    out = []
    for it in items:
        try:
            out.append(it[key])
            continue
        except KeyError:
            out.append(None)
        out.append("tail")
    return out


def g(items, key):
    out = []
    for it in items:
        try:
            if it[key] < 0:
                continue
        except KeyError:
            continue
        out.append(it)
    return out
