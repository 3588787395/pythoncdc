# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b103_map_noguard.pyc (Python 3.11)

def n1(xs):
    for x in xs:
        match x:
            case {'k': v}:
                r = v
                continue
            case _:
                r = 0
    return r
