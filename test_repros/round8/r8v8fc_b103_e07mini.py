
def inner(x):
    match x:
        case [a, b] if a > b:
            return a
        case [a, b]:
            return b
        case a if a is not None:
            return a
        case _:
            return 0
