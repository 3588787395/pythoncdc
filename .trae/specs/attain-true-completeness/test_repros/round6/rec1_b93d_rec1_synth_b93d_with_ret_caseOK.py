# Source Generated with Decompyle++ (Python version)
# File: rec1_b93d_rec1_synth_b93d_with_ret_case.pyc (Python 3.11)

__doc__ = 'R5 synth family 2b: with inside match case with return/assign bodies (B93 phantom ancestor guard).'
def wrc(v):
    match v:
        case 1:
            with _B() as a:
                return a
        case _:
            with _B() as b:
                R = b
    return 0
def wrc_guard(v, g):
    match v:
        case 1 if g:
            with _B() as a:
                R = a
        case 2:
            with _B() as b, _B() as c:
                R = (b, c)
            pass
            pass
    return 1
