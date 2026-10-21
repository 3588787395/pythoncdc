# Source Generated with Decompyle++ (Python version)
# File: rec1_b122c_rec1_synth_b122c_noguard_chain2.pyc (Python 3.11)

__doc__ = 'R5 synth family 5a: nested match no-guard chain with intermediate arm (B122 assembly).'
def nc2(x, y):
    r = 0
    match x:
        case 1:
            match y:
                case 2:
                    r = 21
                case _:
                    r = 22
        case 3:
            r = 3
        case _:
            r = 9
    return r
def nc2_deep(x, y):
    r = 0
    match x:
        case 1:
            match y:
                case 2:
                    r = 21
                case _:
                    r = 22
        case _:
            match y:
                case 3:
                    r = 33
                case _:
                    r = 39
    return r
