# Source Generated with Decompyle++ (Python version)
# File: r5v5_13_for_else_cross.pyc (Python 3.11)

MOD_FE = 0
for _q in range(3):
    if _q > 1:
        break
else:
    MOD_FE = -1
def fe_root(xs):
    for x in xs:
        if x > 10:
            break
    else:
        return 'none'
    return x
class CFe:
    def m(self, xs):
        while xs:
            y = xs.pop()
            if y > 3:
                break
        else:
            return None
        return y
def fe_deep(xs, ys):
    r = 0
    for x in xs:
        if x > 0:
            for y in ys:
                if y > x:
                    r = y
                    break
            else:
                r = x
            continue
        r = 0
    return r
def fe_try(xs):
    try:
        for x in xs:
            if x:
                break
        else:
            r = -1
    finally:
        pass
    return r
def fe_with(xs):
    with open('a') as f:
        for x in xs:
            if x == f.name:
                break
        else:
            r = 0
    return r
def fe_match(xs, n):
    match n:
        case 0:
            for x in xs:
                r = x
            r = -1
        case _:
            r = 1
    return r
def fe_closure(xs):
    def inner():
        for x in xs:
            if x > 1:
                break
        else:
            return 0
        return x
    return inner()
def fe_while_deep(n, m):
    i = 0
    while i < n:
        j = 0
        while j < m:
            if j > 2:
                break
            j += 1
        else:
            i = n
        i += 1
    return -1
