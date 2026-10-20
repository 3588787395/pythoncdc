"""rec1_synth g4a: B70 family — while True + with whole-body forms."""


def g4a_wt_with_pass(p):
    while True:
        with open(p) as f:
            pass


def g4a_wt_with_stmt(p):
    while True:
        with open(p) as f:
            x = 1


def g4a_wt_with_break(p, a):
    while True:
        with open(p) as f:
            if a:
                break
    return 3


def g4a_for_with_pass(xs, p):
    for x in xs:
        with open(p) as f:
            pass
    return 5
