def mc3(x):
    match x:
        case [a, b] if a < b:
            return a
        case _:
            return None
