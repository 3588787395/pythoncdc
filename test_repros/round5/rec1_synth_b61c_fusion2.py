"""R5 synth family 3a: case capture fusion (mapping rest / tuple / class as) with leading if on captures (B61c)."""


def f2_map(x):
    match x:
        case {"op": op, **rest}:
            if "k" in rest:
                del rest["k"]
            return op, rest
        case (p, q):
            if p:
                return p
            return q
        case _:
            raise TypeError("bad")


def f2_cls(x):
    match x:
        case int() as v:
            if v > 0:
                return v
            return -v
        case _:
            return 0
