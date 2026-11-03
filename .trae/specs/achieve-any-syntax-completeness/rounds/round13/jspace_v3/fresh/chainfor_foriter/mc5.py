def mc5(x):
    match x:
        case int(n) if n > 0:
            yield n
        case str(s) if len(s) > 1:
            yield s
        case _:
            yield None
