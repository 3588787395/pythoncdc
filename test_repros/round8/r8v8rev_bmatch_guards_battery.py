def v1(x, g, sink):
    # B77/B81/B103: guard 后跟多语句体（守卫 + 体装配域）
    r = 0
    match x:
        case 1 if g:
            r = 1
            sink.append(r)
        case _:
            r = 2
    return r


def v2(x, y, g, sink):
    # B103: 嵌套 match 臂内 guard（case 体内嵌 match + 守卫）
    r = 0
    match x:
        case 1:
            match y:
                case 2 if g:
                    r = 21
                case _:
                    r = 22
        case _:
            r = 9
    return r


def v3(x, g, sink):
    # B103: or 模式 3 支 + 守卫（任意交替数声明域）
    r = 0
    match x:
        case 1 | 2 | 3 if g:
            r = 'small'
        case 4 | 5:
            r = 'mid'
        case _:
            r = 'other'
    return r


def v4(x, y, g):
    # B81: 真 guard + return 体（守卫 fail 边 + 臂内 return，F1-F4 域外推）
    match x:
        case 7 if g:
            return 'seven'
        case _:
            return y
