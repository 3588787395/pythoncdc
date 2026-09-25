def p_a(xs, flag):
    ys = xs if flag else list(xs)
    del ys[0]
    z = len(ys) * 2
    out = []
    for i in range(z):
        out.append(ys[i])
    return out

def p_b(o, n):
    del o.k
    z = n * 2
    for i in range(z):
        pass
    return z
