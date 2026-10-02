def n_lc_basic(xs):
    out = []
    for x in xs:
        out.append(x * 2)
    return out


def n_sc(xs):
    out = set()
    for x in xs:
        out.add(x % 3)
    return out


def n_dc(pairs):
    out = {}
    for k, v in pairs:
        out[k] = v * 2
    return out


def n_multi_for(a, b):
    out = []
    for x in a:
        for y in b:
            out.append(x + y)
    return out


def n_cond(xs):
    out = []
    for x in xs:
        if x > 0:
            out.append(x)
    return out


def n_nested(mat):
    out = []
    for row in mat:
        inner = []
        for y in row:
            inner.append(y)
        out.append(inner)
    return out
