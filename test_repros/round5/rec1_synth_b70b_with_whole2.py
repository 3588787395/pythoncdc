"""R5 synth family 4b: with as whole while-body + conditional break variants (B70)."""


def ww2(p):
    while True:
        with open(p) as f:
            pass
    return 3


def ww2_flag(p, a):
    while True:
        with open(p) as f:
            if a:
                break
    return 4
