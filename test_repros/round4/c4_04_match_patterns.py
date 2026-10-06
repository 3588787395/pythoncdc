def e01_value(x):
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


def e02_singleton(x):
    for i in range(3):
        match x:
            case None:
                r = 0
            case True:
                r = 1
            case False:
                r = 2
            case object():
                r = 3
    return r


def e03_sequence(x, y, z):
    if x:
        match y:
            case [a, b, c]:
                r = a + b + c
            case [a, *rest]:
                r = a
            case (a, b):
                r = a - b
            case _:
                r = 0
    return r


def e04_mapping(x):
    while x:
        match x:
            case {'a': 1, 'b': b}:
                r = b
            case {'k': v, **rest}:
                r = v
            case _:
                r = 0
    return r


def e05_class_kw(x):
    try:
        match x:
            case Point(x=0, y=0):
                r = 'origin'
            case Point(x=px, y=py):
                r = px + py
            case _:
                r = 0
    finally:
        pass
    return r


def e06_or_guard(x):
    with ctx():
        match x:
            case 1 | 2 | 3 if x > 1:
                r = 'small'
            case 4 | 5 if x > 4:
                r = 'mid'
            case _:
                r = 'other'
    return r


def e07_capture(x, y):
    def inner():
        match x:
            case [a, b] if a > b:
                return a
            case [a, b]:
                return b
            case a if a is not None:
                return a
            case _:
                return 0
    return inner()


def e08_star_nest(x):
    match x:
        case [1, *mid, 9]:
            r = mid
        case {'key': [first, *rest]}:
            r = first
        case (head, *tail):
            r = tail
        case _:
            r = None
    return r


def e09_nested_match(x, y):
    match x:
        case [a, b]:
            match a:
                case 1:
                    r = 'a1'
                case _:
                    r = 'ax'
        case _:
            match y:
                case 2:
                    r = 'y2'
                case _:
                    r = 'yx'
    return r


class CM:
    def m(self, x):
        match x:
            case {'a': v} if v:
                return v
            case [*items]:
                return items
            case _:
                return None
