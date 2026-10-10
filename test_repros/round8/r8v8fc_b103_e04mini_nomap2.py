
def e04b(x):
    while x:
        match x:
            case {'a': 1, 'b': b}:
                r = b
            case _:
                r = 0
    return r
