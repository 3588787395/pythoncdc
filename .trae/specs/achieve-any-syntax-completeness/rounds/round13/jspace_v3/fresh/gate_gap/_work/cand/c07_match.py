def _host():
    pass

def outer(v):
    match v:
        case 1:
            r = 'one'
        case 2:
            r = 'two'
        case _:
            r = 'other'
    return r
