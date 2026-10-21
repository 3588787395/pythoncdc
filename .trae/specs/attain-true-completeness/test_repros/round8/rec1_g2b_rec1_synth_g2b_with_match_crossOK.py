# Source Generated with Decompyle++ (Python version)
# File: rec1_g2b_rec1_synth_g2b_with_match_cross.pyc (Python 3.11)

__doc__ = 'rec1_synth g2b: with×match bidirectional host family — 4-deep match-in-with-in-match cross.'
def g2b_deep_cross(v, p, flag):
    match v:
        case {'op': op}:
            with open(p) as f:
                match op:
                    case 'r':
                        return (op, f)
                    case _:
                        while False:
                            pass
                        return (flag, f)
        case _:
            pass
def g2b_with_match_with(v, p):
    with open(p) as f:
        match v:
            case [a, b]:
                with open(p) as g:
                    return (a, b, f, g)
            case _:
                return (f,)
    return ()
