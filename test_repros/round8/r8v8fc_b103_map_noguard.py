
def n1(xs):
    for x in xs:
        match x:
            case {'k': v}:
                r = v
            case _:
                r = 0
    return r
