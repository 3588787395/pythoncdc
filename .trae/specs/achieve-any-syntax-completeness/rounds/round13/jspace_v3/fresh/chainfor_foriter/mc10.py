def mc10(x, y):
    match x:
        case int(n) if n > 1:
            yield n + y
        case str(s) if s:
            yield s * 2
        case _:
            yield y
