def f(values):
    if len(values) > 3:
        raise ValueError("too many")
    if len(values) >= 2:
        if not isinstance(values[1], str):
            raise ValueError("second")
    return str(*values)
