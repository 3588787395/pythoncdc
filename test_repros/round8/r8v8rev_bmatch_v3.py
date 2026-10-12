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


