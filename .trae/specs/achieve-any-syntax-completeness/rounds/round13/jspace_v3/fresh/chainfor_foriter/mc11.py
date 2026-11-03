def mc11(x):
    match x:
        case int(n) if n > 0:
            return n * 2
        case _:
            return 0
