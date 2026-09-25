def p1(d):
    try:
        x = d['a']
        return None
    except KeyError:
        return None


def p2(d):
    try:
        x = d['a']
        if x:
            return None
    except KeyError:
        print(x)


def p3(d, k):
    if k:
        try:
            y = d[k]
            try:
                z = y[k]
                return None
            except KeyError:
                y[k] = 1
        except KeyError:
            return None
    else:
        return d


def p4(d, k):
    try:
        return None
    except KeyError:
        return None


def p5(d, k):
    try:
        v = d[k]
        for i in v:
            if i:
                return None
    except KeyError:
        print(k)


def p6(d, k):
    try:
        v = d[k]
        while v:
            v -= 1
        return None
    except KeyError:
        return 1


def p7(d, k):
    try:
        v = d[k]
        return None
    finally:
        print(v)


def p8(d, k):
    try:
        try:
            v = d[k]
            return None
        except KeyError:
            return 2
    except TypeError:
        return 3
