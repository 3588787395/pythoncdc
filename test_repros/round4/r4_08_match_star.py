# r4_08 attack: star patterns ([1, *rest])


def match_star_tail(seq):
    """Attack 1: star capture at tail."""
    match seq:
        case [1, *rest]:
            return rest
        case [*other]:
            return other


def match_star_head(seq):
    """Attack 2: star capture in the middle."""
    match seq:
        case [*head, last]:
            return (len(head), last)
        case _:
            return "nolist"


def match_star_double(seq):
    """Attack 3: two star captures."""
    match seq:
        case [*first, x, y]:
            return (first, x, y)
        case _:
            return "short"


def match_star_tuple(seq):
    """Attack 4: star in tuple pattern."""
    match seq:
        case (a, *mid, b):
            return (a, mid, b)
        case _:
            return "notuple"


def match_star_literal_head(seq):
    """Attack 5: star with literal heads on both sides."""
    match seq:
        case [0, *mid, 0]:
            return ("wrapped", mid)
        case [0, *tail]:
            return ("head", tail)
        case [*init, 0]:
            return ("tail", init)
        case _:
            return "nozero"


def match_star_body_work(seq):
    """Attack 6: star pattern case with loop body."""
    out = []
    match seq:
        case [lead, *rest]:
            out.append(lead)
            for item in rest:
                out.append(item + 1)
        case _:
            out.append("empty")
    return out
