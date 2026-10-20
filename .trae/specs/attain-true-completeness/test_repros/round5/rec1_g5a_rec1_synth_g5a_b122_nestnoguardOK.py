# Source Generated with Decompyle++ (Python version)
# File: rec1_g5a_rec1_synth_g5a_b122_nestnoguard.pyc (Python 3.11)

__doc__ = 'rec1_synth g5a: B122 family — nested match no-guard (with defaults) at depth.'
def g5a_nested_noguard(x, y):
    if x:
        match x:
            case 1:
                match y:
                    case 2:
                        return 21
                    case _:
                        return 22
            case _:
                return 9
    else:
        return 0
def g5a_nested_in_for(x, y, xs):
    for i in xs:
        match x:
            case 1:
                match y:
                    case 2:
                        return (i, 21)
                    case _:
                        return (i, 22)
            case _:
                return 9
    return 0
