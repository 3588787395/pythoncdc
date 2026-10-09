# Source Generated with Decompyle++ (Python version)
# File: r4v4r_b103_guard.pyc (Python 3.11)

class GT:
    def m(self, x):
        match x:
            case {'a': v}:
                return v
            case _:
                pass
def none_guard(x):
    match x:
        case a if a is not None:
            return a
        case None if a is None:
            return 0
        case _:
            return 1
def cmp_guard(x):
    y = x
    if y > 3:
        return y
    else:
        return 0
def real_ternary(c, x, y):
    return x if c else y
def real_if(c, x):
    if c:
        return x
    else:
        return -1
def nested_guard(xs):
    for x in xs:
        match x:
            case {'k': v}:
                r = v
                continue
            case _:
                r = 0
    return r
