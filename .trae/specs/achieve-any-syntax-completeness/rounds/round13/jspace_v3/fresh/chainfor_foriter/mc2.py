def mc2(x):
    match x:
        case int(n) if n > 0:
            yield n
        case _:
            yield 0
