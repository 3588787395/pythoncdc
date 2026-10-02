# rv4 (REVIEW2 variant): B18 - class pattern multi-keyword out-of-order slots,
# positional/keyword mixed, guard containing function calls


class P3:
    __match_args__ = ("x", "y", "z")

    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z


def kw_disorder(p):
    """V1: keyword patterns in order different from declaration; literal in middle."""
    match p:
        case P3(z=0, y=0, x=0):
            return "origin"
        case P3(z=zz, y=0, x=0):
            return ("z", zz)
        case P3(x=a, z=c, y=9):
            return ("xzc", a, c)
        case _:
            return "no"


def mixed_pos_kw(p):
    """V2: positional + keyword mixed in one pattern."""
    match p:
        case P3(0, 0, z=0):
            return "pos-kw"
        case P3(xx, 0, z=zz):
            return (xx, zz)
        case _:
            return "no"


def guard_call(p):
    """V3: guards with function calls and arithmetic mixed."""
    match p:
        case P3(x=a, y=b) if abs(a) + abs(b) <= 1 and max(a, 0) >= -1:
            return "in-unit"
        case P3(x=a, y=b) if min(a, b) < 0:
            return "neg"
        case P3(x=a, y=b, z=c) if a * b + c > 10:
            return ("big", a, b, c)
        case _:
            return "out"
