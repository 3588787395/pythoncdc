# Source Generated with Decompyle++ (Python version)
# File: rec1_b93c_rec1_synth_b93c_alt3.pyc (Python 3.11)

__doc__ = 'R5 synth family 2a: with/match alternation depth 3 + match-in-with (B93 cross-body ancestor).'
def alt3(v):
    if v == 1:
        with _B() as a:
            if a == 2:
                with _B() as b:
                    R = (a, b)
    return 1
def miw(v):
    with _B() as a:
        match v:
            case 1:
                R = a
            case 2 if a:
                R = 2
    return 2
