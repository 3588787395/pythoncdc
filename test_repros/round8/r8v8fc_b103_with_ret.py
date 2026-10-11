def w_ret(x):
    with ctx():
        r = x
    return r


def w_match_ret(x):
    with ctx():
        match x:
            case 1:
                r = 'one'
            case _:
                r = 'other'
    return r
