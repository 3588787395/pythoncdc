# Source Generated with Decompyle++ (Python version)
# File: rec1_synth_g4b_b70_whiletrue_with.pyc (Python 3.11)

"""rec1_synth g4b: B70 family — while True + with with real break/continue + while-cond mirror."""
def g4b_wt_with_continue(p, a):
    while True:
        with open(p) as f:
            if a:
                continue
            pass
            return 4
def g4b_while_cond_with(p):
    while p:
        with open(p) as f:
            pass
    return 5
def g4b_wt_with_noas(p):
    while 1:
        with open(p):
            pass
def g4b_wt_nested_with(p, a):
    while True:
        with open(p) as f, open(p) as g:
            if a:
                break
    return 6
