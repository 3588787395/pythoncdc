def v1(a, b, d, e, k, v):
    # B107-R2 正例：4 目标混合链（首目标简单名 + 3 复杂目标，交错 COPY 任意 N 声称域）
    a = b.c = d[k] = e.f = v
    return a, b.c, d[k], e.f


def v2(o, p, k, v):
    # B107-R2 邻例：3 目标复杂链 + 链后接 return（同块 return 后继位形）
    o.a = p[k] = o.b = v
    return v


def v3(a, b, d, e, k, v):
    # B107-R2 正例：4 目标全复杂链（交错 COPY 不变式 4 段外推）
    b.c = d[k] = e.f = a.g = v
    return b.c, d[k], e.f, a.g
