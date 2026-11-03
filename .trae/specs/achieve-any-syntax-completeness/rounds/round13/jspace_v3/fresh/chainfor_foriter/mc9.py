def mc9(pairs):
    match pairs:
        case {'a': a, 'b': b} if a < b:
            yield (a, b)
        case _:
            yield None
