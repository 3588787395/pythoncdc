# Source Generated with Decompyle++ (Python version)
# File: r4_03_match_sequence.pyc (Python 3.11)

def match_seq_list2(seq):
    """Attack 1: two-element list pattern."""
    match seq:
        case [a, b]:
            return a + b
        case _:
            return None
def match_seq_tuple3(seq):
    """Attack 2: three-element tuple pattern."""
    match seq:
        case [x, y, z]:
            return (z, y, x)
        case _:
            return ()
def match_seq_nested(seq):
    """Attack 3: nested sequence pattern [[a, b], c]."""
    match seq:
        case [[a, b], c]:
            return (a, b, c)
        case [[a], b]:
            return (a, b, 0)
        case _:
            return 'nomatch'
def match_seq_deep_nested(seq):
    """Attack 4: deeply nested sequence pattern [1, [2, [3, x]]]."""
    match seq:
        case [1, [2, [3, x]]]:
            return x
        case [1, [2, rest]]:
            return rest
        case _:
            return -1
def match_seq_mixed_literal(seq):
    """Attack 5: sequence with literal heads [0, x] / [1, y]."""
    match seq:
        case [0, x]:
            return ('zero', x)
        case [1, y]:
            return ('one', y)
        case [a, b]:
            return ('pair', a, b)
        case _:
            return 'empty'
def match_seq_open_ended(seq):
    """Attack 6: open-ended sequence [first, *mid, last]."""
    match seq:
        case [first, *mid, last]:
            return (first, len(mid), last)
        case []:
            return 'empty'
        case _:
            return 'noseq'
