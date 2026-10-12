def n1(x, y, g):
    # 嵌套 match 无守卫（e09 域对照）
    r = 0
    match x:
        case 1:
            match y:
                case 2:
                    r = 21
                case _:
                    r = 22
        case _:
            r = 9
    return r
