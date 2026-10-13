def v1(x, g):
    # B103-R2 or 支数外推：or 4 支 + 裸名守卫（S 点 POP_TOP 丢弃段协议任意支数声称域）
    r = 0
    match x:
        case 1 | 2 | 3 | 4 if g:
            r = 'small'
        case 5 | 6:
            r = 'mid'
        case _:
            r = 'other'
    return r


def v2(x, g, h):
    # B103-R2 邻例：or 支 + 复合守卫（g and h 布尔短路守卫，跨块 fail 边位形）
    r = 0
    match x:
        case 1 | 2 if (g and h):
            r = 'both'
        case 3:
            r = 'three'
        case _:
            r = 'other'
    return r


def v3(x, g):
    # B103-R2 邻例：or 4 支 + 比较形守卫（w1 比较形保真口径的支数外推对照）
    r = 0
    match x:
        case 1 | 2 | 3 | 4 if x > 1:
            r = 'small'
        case _:
            r = 'other'
    return r
