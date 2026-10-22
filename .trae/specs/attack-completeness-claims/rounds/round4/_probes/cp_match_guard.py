def f(v):
    match v:
        case 1 if v > 0:
            return "a"
        case _:
            return "b"
