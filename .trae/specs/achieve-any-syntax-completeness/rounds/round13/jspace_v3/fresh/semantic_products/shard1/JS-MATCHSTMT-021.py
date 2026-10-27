# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_b122d_triple_nest.pyc (Python 3.11)

"""R5 synth family 5b: triple-nested match, case-head inner chain, guard at innermost (B122 convergence)."""
def tn(x, y, z, g):
    r = 0
    match x:
        case 1:
            match y:
                case 2:
                    match z:
                        case 3 if g:
                            r = 33
                        case _:
                            r = 30
                case _:
                    r = 20
        case _:
            r = 9
    return r
def tn2(x, y, z):
    r = 0
    match x:
        case 1:
            match y:
                case 2:
                    match z:
                        case 3:
                            r = 3
                        case _:
                            r = 30
                case _:
                    r = 20
        case _:
            r = 9
    return r
