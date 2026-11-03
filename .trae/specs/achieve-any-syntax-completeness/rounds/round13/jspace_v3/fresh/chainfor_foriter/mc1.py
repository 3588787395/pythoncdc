def mc1(cls):
    v = cls.__dict__.get('__slots__')
    match v:
        case None:
            return
        case str(slot):
            yield slot
        case iterable if not hasattr(iterable, '__next__'):
            yield from iterable
        case _:
            raise TypeError('bad')
