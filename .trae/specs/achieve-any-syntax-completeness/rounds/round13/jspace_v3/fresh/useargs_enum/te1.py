def te1(cls, bases, cd, metacls, kwds):
    try:
        exc = None
        enum_class = super().__new__(metacls, cls, bases, cd, **kwds)
    except RuntimeError as e:
        exc = e.__cause__ or e
    if exc is not None:
        raise exc
    return enum_class
