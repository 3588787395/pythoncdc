def mA(v, flag):
    r = 0
    match v:
        case int(n) if n > 0 or flag:
            r = 1
        case _:
            r = 0
    return r


def mB(v, flag, p):
    with open(p) as f:
        r = 0
        match v:
            case int(n) if n > 0 or flag:
                r = 1
            case _:
                r = 0
        r += f is None
    return r


def mC(v):
    match v:
        case {'op': op, **rest}:
            if 'tmp' in rest:
                del rest['tmp']
            return op, rest
        case _:
            return None


def mD(v):
    for x in range(1):
        match v:
            case {'op': op, **rest}:
                if 'tmp' in rest:
                    del rest['tmp']
                return op, rest
            case _:
                return None
    return None


def mE(x, g):
    r = 0
    match x:
        case [int(a), *rest] if rest:
            r = (a, len(rest))
        case _:
            r = 'other'
    return r


def mF(x, g):
    r = 0
    match x:
        case 1 if g:
            r = 1
        case 2:
            r = 2
        case _ if not g:
            r = -1
    return r


def mG(v, flag):
    if flag:
        r = 0
        match v:
            case int(n) if n > 0 or flag:
                r = 1
            case _:
                r = 0
        return r
    return -1
