
def n2(xs):
    for x in xs:
        match x:
            case {'k': v} if v is not None:
                r = v
            case _:
                r = 0
    return r
