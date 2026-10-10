# Source Generated with Decompyle++ (Python version)
# File: r8v8fc_b103_e04mini.pyc (Python 3.11)

def e04(x):
    while x:
        match x:
            case {'a': 1, 'b': b}:
                r = b
            case {'k': v, **rest}:
                r = v
            case _:
                r = 0
    return r
