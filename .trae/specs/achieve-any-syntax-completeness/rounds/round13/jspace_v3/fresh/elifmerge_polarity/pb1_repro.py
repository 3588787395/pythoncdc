def f(values):
    if len(values) > 3:
        raise ValueError("too many")
    if len(values) == 1:
        if not isinstance(values[0], str):
            raise ValueError("first")
    if len(values) >= 2:
        if not isinstance(values[1], str):
            raise ValueError("second")
    if len(values) == 3:
        if not isinstance(values[2], str):
            raise ValueError("third")
    return str(*values)
