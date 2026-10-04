# Source Generated with Decompyle++ (Python version)
# File: b74_a_noimport.pyc (Python 3.11)

def f(rows):
    for row in rows:
        match row:
            case {'k': v}:
                if v > 0:
                    return wrap(v)
                else:
                    continue
            case _:
                pass
    return base_value
