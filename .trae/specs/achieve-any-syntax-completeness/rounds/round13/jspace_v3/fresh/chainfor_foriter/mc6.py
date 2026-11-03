def mc6(items):
    match items:
        case list(xs) if xs:
            total = 0
            for v in xs:
                total += v
            yield total
        case _:
            yield 0
