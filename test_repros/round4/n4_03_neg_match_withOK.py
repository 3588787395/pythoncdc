# Source Generated with Decompyle++ (Python version)
# File: n4_03_neg_match_with.pyc (Python 3.11)

def n_match_value(x):
    match x:
        case 1:
            return 'one'
        case _:
            return 'other'
def n_match_seq(x):
    match x:
        case [a, b]:
            return a + b
        case _:
            return 0
def n_multi_with(a, b):
    with open(a) as f, open(b) as g:
        return f.read() + g.read()
        return None
def n_global():
    global _NEG
    _NEG = 1
    return _NEG
