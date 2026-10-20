# Source Generated with Decompyle++ (Python version)
# File: rec1_g5b_rec1_synth_g5b_b122_guards_battery.pyc (Python 3.11)

__doc__ = 'rec1_synth g5b: B122 family — nested guard-in-arm + or-pattern guard assembly.'
def g5b_nested_guard_arm(x, y, g):
    match x:
        case 1:
            match y:
                case 2 if g:
                    return 21
                case _:
                    return 22
        case _:
            return 9
def g5b_orpat_guard(x, g):
    match x:
        case 1 | 2 | 3 if g:
            return 'small'
        case 4 | 5:
            return 'mid'
        case _:
            return 'other'
def g5b_guard_return(x, g):
    match x:
        case 7 if g:
            return 'seven'
        case _:
            return 'rest'
