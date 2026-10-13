def v1(y, e):
    # B104 域邻探查：for 宿主 4 元链 + or 尾（链+or 混合，and 尾声称域外）
    out = []
    for a in y:
        if 0 < a < b < c < d or e:
            pass
    return out


def v2(y, e):
    # B104 域邻探查（修正命名绑定）：for 宿主 4 元链 + or 尾
    out = []
    for i in y:
        b, c, d = i, i, i
        if 0 < i < b < c < d or e:
            out.append(i)
    return out
