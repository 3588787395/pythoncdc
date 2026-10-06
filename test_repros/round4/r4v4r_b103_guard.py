class GT:
    def m(self, x):
        match x:
            case {'a': v} if v:
                return v
            case _:
                return None


def none_guard(x):
    match x:
        case a if a is not None:
            return a
        case a if a is None:
            return 0
        case _:
            return 1


def cmp_guard(x):
    match x:
        case y if y > 3:
            return y
        case _:
            return 0


def real_ternary(c, x, y):
    return x if c else y


def real_if(c, x):
    if c:
        return x
    return -1


def nested_guard(xs):
    for x in xs:
        match x:
            case {'k': v} if v is not None:
                r = v
            case _:
                r = 0
    return r