
def n3(x):
    match x:
        case a if a is not None:
            return a
        case a if a is None:
            return 0
        case _:
            return 1
