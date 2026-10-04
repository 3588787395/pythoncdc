# Source Generated with Decompyle++ (Python version)
# File: b74_b_import.pyc (Python 3.11)

def f(rows):
    for row in rows:
        match row:
            case {'k': v}:
                from m9 import wrap
                if v > 0:
                    return wrap(v)
                else:
                    continue
            case _:
                pass
    return base_value
