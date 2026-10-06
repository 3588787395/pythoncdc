def e01_root(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    elif x == 3:
        return 'c'
    elif x == 4:
        return 'd'
    else:
        return 'e'


def e02_shallow(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    return 'c'


def e03_nested_if(x, y):
    if y > 0:
        if x == 1:
            r = 1
        elif x == 2:
            r = 2
        elif x == 3:
            r = 3
        else:
            r = 4
    else:
        if x == 1:
            r = 5
        elif x == 2:
            r = 6
        else:
            r = 7
    return r


class CE:
    def m(self, x):
        for i in range(3):
            if x == i:
                v = 'a'
            elif x == i + 1:
                v = 'b'
            elif x == i + 2:
                v = 'c'
            else:
                v = 'd'
        return v


def e04_deep(x, y, z):
    while x > 0:
        if y > 0:
            if z == 1:
                r = 1
            elif z == 2:
                r = 2
            else:
                r = 3
        elif y < 0:
            if z == 1:
                r = 4
            elif z == 2:
                r = 5
            else:
                r = 6
        else:
            r = 7
        x -= 1
    return r


def e05_try_host(x):
    try:
        if x == 1:
            r = 'a'
        elif x == 2:
            r = 'b'
        elif x == 3:
            r = 'c'
        else:
            r = 'd'
    finally:
        r = r
    return r


def e06_with_host(x):
    with open('t') as f:
        if x == 1:
            r = 1
        elif x == 2:
            r = 2
        elif x == 3:
            r = 3
        else:
            r = 4
    return r


def e07_match_host(x):
    match x:
        case 0:
            if x == 1:
                r = 1
            elif x == 2:
                r = 2
            elif x == 3:
                r = 3
            else:
                r = 4
        case _:
            r = 0
    return r


def e08_closure_host(x):
    def inner():
        if x == 1:
            return 1
        elif x == 2:
            return 2
        elif x == 3:
            return 3
        return 4
    return inner()


def e09_comp_host(xs):
    return [1 if x == 1 else (2 if x == 2 else (3 if x == 3 else 0)) for x in xs]


_G = 3
if _G > 1:
    _r = 'a'
elif _G > 2:
    _r = 'b'
elif _G > 3:
    _r = 'c'
else:
    _r = 'd'
