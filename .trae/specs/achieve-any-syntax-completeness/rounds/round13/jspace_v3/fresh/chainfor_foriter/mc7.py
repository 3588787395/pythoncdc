def mc7(x, lim):
    match x:
        case int(n) if n > 0:
            if n > lim:
                yield n
            else:
                yield lim
        case _:
            yield 0
