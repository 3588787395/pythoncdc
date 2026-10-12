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


