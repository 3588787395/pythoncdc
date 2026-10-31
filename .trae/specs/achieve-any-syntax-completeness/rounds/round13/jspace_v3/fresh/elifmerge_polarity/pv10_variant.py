def f(values, tag):
    if tag:
        raise ValueError("tagged")
    if len(values) >= 2:
        if not isinstance(values[1], str):
            raise ValueError("second")
    if not values:
        raise ValueError("empty")
    return len(values)
