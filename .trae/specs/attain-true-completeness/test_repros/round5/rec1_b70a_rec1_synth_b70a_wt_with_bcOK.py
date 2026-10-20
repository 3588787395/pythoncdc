# Source Generated with Decompyle++ (Python version)
# File: rec1_b70a_rec1_synth_b70a_wt_with_bc.pyc (Python 3.11)

__doc__ = 'R5 synth family 4a: while True + with break/continue (B70 exit-path classification).'
def wbc(p, a, b):
    while True:
        with open(p) as f:
            if a:
                break
            if b:
                continue
            use(f)
    return 1
def wbc_nested(p, q, a):
    while True:
        with open(p) as f, open(q) as g:
            if a:
                break
        break
    return 2
