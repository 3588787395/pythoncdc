# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b103_nested_guard.pyc (Python 3.11)

def n2(xs):
    for x in xs:
        match x:
            case {'k': v} if v is not None:
                r = v
                continue
            case _:
                r = 0
    return r
