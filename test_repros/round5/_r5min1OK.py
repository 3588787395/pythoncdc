# Source Generated with Decompyle++ (Python version)
# File: _r5min1.pyc (Python 3.11)

def mA(v, flag):
    r = 0
    match v:
        case int(n) if flag:
            if n > 0 or flag:
                r = 1
            else:
                r = 0
        case _:
            pass
    return r
def mB(v, flag, p):
    with open(p) as f:
        r = 0
        match v:
            case int(n) if flag:
                if n > 0 or flag:
                    r = 1
                else:
                    r = 0
            case _:
                pass
    return r
def mC(v):
    match v:
        case {'op': op, **rest}:
            if 'tmp' in rest:
                del rest['tmp']
            return (op, rest)
        case _:
            pass
def mD(v):
    for x in range(1):
        match v:
            case {'op': op, **rest}:
                if 'tmp' in rest:
                    del rest['tmp']
                else:
                    return (op, rest)
            case _:
                break
def mE(x, g):
    r = 0
    match x:
        case [_, *_] if rest:
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
        case _:
            r = -1
    return r
def mG(v, flag):
    if flag:
        r = 0
        match v:
            case int(n) if flag:
                if n > 0 or flag:
                    r = 1
                else:
                    r = 0
            case _:
                pass
        return r
    else:
        return -1
