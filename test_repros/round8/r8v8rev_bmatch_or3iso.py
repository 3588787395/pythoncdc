def w1(x, g):
    # 3 支 or + 比较守卫
    r = 0
    match x:
        case 1 | 2 | 3 if x > 1:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r


def w2(x, g):
    # 2 支 or + 裸名守卫
    r = 0
    match x:
        case 1 | 2 if g:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r


def w3(x, g):
    # 3 支 or + 裸名守卫（本体重放）
    r = 0
    match x:
        case 1 | 2 | 3 if g:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r


def w4(x, g):
    # 单字面量 + 裸名守卫（B81 域对照）
    r = 0
    match x:
        case 1 if g:
            r = 'one'
        case _:
            r = 'other'
    return r
