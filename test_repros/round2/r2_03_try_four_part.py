# r2_03 try/except/else/finally 四段全
# 焦点：四段全形态 + else 段


def f(x, d):
    out = {}
    try:
        v = d["k"]
    except KeyError:
        v = 0
    else:
        v += 1
    finally:
        out["done"] = True
    out["v"] = v
    return out


def g(items, key):
    res = []
    for it in items:
        try:
            val = it[key]
        except (KeyError, TypeError):
            val = None
        else:
            val = val * 2
        finally:
            res.append("step")
        res.append(val)
    return res
