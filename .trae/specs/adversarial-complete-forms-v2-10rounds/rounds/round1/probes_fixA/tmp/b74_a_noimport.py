def f(rows):
    for row in rows:
        match row:
            case {"k": v}:
                if v > 0:
                    return wrap(v)
    return base_value
