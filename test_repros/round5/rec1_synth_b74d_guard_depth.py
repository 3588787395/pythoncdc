"""R5 synth family 1a: match guard depth (or-pattern + sequence star + mapping rest + class as, all guarded)."""


def gd_or_seq_guard(x, g):
    r = 0
    match x:
        case 1 | 2 | 3 if g:
            r = 'small'
        case [int(a), *rest] if rest:
            r = (a, len(rest))
        case _:
            r = 'other'
    return r


def gd_map_class_guard(x, g):
    match x:
        case {"op": op, **kw} if op:
            return op, len(kw)
        case int() as v if v > 0:
            return v * 2
        case _:
            return None
