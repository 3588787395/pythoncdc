# Source Generated with Decompyle++ (Python version)
# File: r7_synth_b144_for_else_break.pyc (Python 3.11)

def s_b144_for_else_break(xs):
    for i, v in enumerate(xs):
        if v is None:
            del xs[i]
            break
    else:
        raise ValueError('no None')
    return xs
def s_b144_for_else_break2(xs):
    out = []
    for v in xs:
        if v < 0:
            out.append(v)
            break
    else:
        out.append('all')
    return out
