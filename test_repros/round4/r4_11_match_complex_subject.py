# r4_11 attack: match subject as complex expressions (attr chain / tuple / call)


class Cfg:
    def __init__(self, mode, level):
        self.mode = mode
        self.level = level

    def inner(self):
        return Cfg("inner", 7)


def match_subject_attr_chain(obj):
    """Attack 1: subject = attribute chain."""
    match obj.inner().mode:
        case "inner":
            return "got-inner"
        case "outer":
            return "got-outer"
        case _:
            return "unknown-mode"


def match_subject_call(x):
    """Attack 2: subject = function call."""
    match sorted(x):
        case [a, b, c]:
            return (a, b, c)
        case _:
            return tuple(sorted(x))


def match_subject_tuple_expr(a, b, c):
    """Attack 3: subject = tuple built from expressions."""
    match (a + 1, b * 2, c - 3):
        case (0, 0, 0):
            return "triple-zero"
        case (x, 0, z):
            return ("mid-flat", x, z)
        case (x, y, z):
            return (x, y, z)


def match_subject_subscript(d):
    """Attack 4: subject = subscript expression."""
    match d["key"]:
        case 1:
            return "one"
        case 2:
            return "two"
        case _:
            return "missing"


def match_subject_attr_tuple(obj):
    """Attack 5: subject = tuple of attribute accesses."""
    match (obj.mode, obj.level):
        case ("a", 1):
            return "a1"
        case ("b", 2):
            return "b2"
        case (m, lvl):
            return (m, lvl)


def match_subject_method_chain(obj):
    """Attack 6: subject = chained method call with literal cases."""
    match obj.inner().inner().level:
        case 7:
            return "seven"
        case 14:
            return "fourteen"
        case _:
            return "other-level"
