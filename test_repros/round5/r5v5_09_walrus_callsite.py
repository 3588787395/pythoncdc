def w_root(x):
    if (n := len(x)) > 3:
        return n
    return 0


def w_call(f, x):
    return f((n := x + 1), n)


def w_nested_call(f, g, x):
    return f((a := g(x)), (b := a + 1))


def w_deep(xs):
    r = 0
    for x in xs:
        while (m := x * 2) < 20:
            if m:
                r = m
            x += 1
    return r


class CW:
    def m(self, x):
        if (k := x + 1) > 0:
            return k
        return (j := x)


def w_comp(xs):
    return [y for x in xs if (y := x * 2) > 4]


def w_with(x):
    with open('a') as f:
        if (line := f.readline()) > '':
            return line
    return ''


def w_match(x):
    match x:
        case 0:
            return (n := x + 1)
        case _:
            return (m := x - 1)


def w_boolop(a, b):
    r = (x := a) and (y := b)
    return r
