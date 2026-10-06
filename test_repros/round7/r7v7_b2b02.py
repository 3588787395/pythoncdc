def b2b02_shallow(xs, flag):
    for x in xs:
        if x is None:
            return False
    return True


def b2b02_deep(xs, flag):
    n = 0
    for x in xs:
        if flag:
            if x > 0:
                if x is None:
                    return False
                n += 1
    return n
