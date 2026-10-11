def f(x):
    if x > 0:
        match x:
            case 1:
                r = 'one'
            case 2:
                r = 'two'
            case 3 | 4:
                r = 'few'
            case _:
                r = 'many'
    else:
        r = 'neg'
    return r
