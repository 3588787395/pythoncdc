def f(x):
    match x:
        case 1 | 2 | 3 if x > 1:
            r = 'small'
        case 4 | 5 if x > 4:
            r = 'mid'
        case _:
            r = 'other'
    return r
