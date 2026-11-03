def g(cls, flag):
    d = dict(cls.__dict__)
    d['k'] = tuple(f2(d, ('w',) if flag else ()))
    for x in d:
        yield x
