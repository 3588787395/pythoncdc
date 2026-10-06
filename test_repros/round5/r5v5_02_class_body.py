class Doc:
    """class docstring here（类体 docstring 位）"""
    X = 1
    Y: int = 2
    Z: str
    W = X + Y

    class Inner:
        """inner class docstring"""
        I = 3
        J: int = 4

        class Inner2:
            K = 5

    def __init__(self, v):
        self.v = v
        self.a: int = 0

    def method(self, xs):
        r = 0
        for x in xs:
            if x > 0:
                r += x
            elif x < 0:
                r -= x
            else:
                r = 0
        self.a += r
        return f'{r!r}'

    @property
    def prop(self):
        return self.v


class Ctl:
    FLAG = 3
    if FLAG > 1:
        A = 1
        B = 2
    else:
        A = 0
        B = 0
    for _k in range(2):
        C = _k
    try:
        D = 1
    except Exception:
        D = 2
    with open('a') as f:
        E = f
    match FLAG:
        case 3:
            F = 'three'
        case _:
            F = 'other'
    G = [q for q in range(3)]
    H = f'{FLAG}'
