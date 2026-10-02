# Source Generated with Decompyle++ (Python version)
# File: r4_08_match_star.pyc (Python 3.11)

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
def match_star_double(seq):
    """Attack 3: two star captures."""
    match seq:
        case [*first, x, y]:
            return (first, x, y)
def match_star_tuple(seq):
    """Attack 4: star in tuple pattern."""
    match seq:
        case [a, *mid, b]:
            return (a, mid, b)
def match_star_literal_head(seq):
    """Attack 5: star with literal heads on both sides."""
    match seq:
        case [0, *mid, 0]:
            return ('wrapped', mid)
        case [0, *tail]:
            return ('head', tail)
        case [*init, 0]:
            return ('tail', init)
def match_star_body_work(seq):
    """Attack 6: star pattern case with loop body."""
    match seq:
        case [lead, *rest]:
            out.append(lead)
            for item in rest:
                out.append(item + 1)
            return out
        case _:
            out.append('empty')
