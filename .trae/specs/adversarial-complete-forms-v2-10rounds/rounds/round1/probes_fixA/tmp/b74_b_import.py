def f(rows):
    for row in rows:
        match row:
            case {"k": v}:
                from m9 import wrap
                if v > 0:
                    return wrap(v)
    return base_value
