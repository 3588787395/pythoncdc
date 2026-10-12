def v4(x, y, g):
    # B81: 真 guard + return 体（守卫 fail 边 + 臂内 return，F1-F4 域外推）
    match x:
        case 7 if g:
            return 'seven'
        case _:
            return y
