def g2(cls, weakref_slot, field_names):
    cls_dict = dict(cls.__dict__)
    inherited = set(map(iter, cls.__mro__[1:-1]))
    cls_dict['__slots__'] = tuple(filter(inherited.__contains__, (field_names, ('__weakref__',) if weakref_slot else ())))
    for name in field_names:
        cls_dict.pop(name, None)
    return cls_dict
