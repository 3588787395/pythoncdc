def mc4(seq):
    match seq:
        case it if not hasattr(it, '__next__'):
            yield from it
        case _:
            raise ValueError('no')
