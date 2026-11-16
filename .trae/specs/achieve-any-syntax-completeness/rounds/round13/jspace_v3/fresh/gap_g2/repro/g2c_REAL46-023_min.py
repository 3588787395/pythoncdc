# g2c REAL46-023 min: the `...` const must stay Ellipsis (pre-rr-v5r85 loader -> None).
names = {bool: 'NameConstant', type(None): 'NameConstant', int: 'Num',
         str: 'Str', bytes: 'Bytes', type(...): 'Ellipsis'}
types = {Ellipsis: (type(...),)}
print(len(names), names.get(type(None)), types[Ellipsis])
