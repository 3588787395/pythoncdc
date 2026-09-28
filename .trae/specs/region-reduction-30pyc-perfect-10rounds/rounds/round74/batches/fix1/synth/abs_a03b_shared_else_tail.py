# synth a03b -- shared else + trailing statement inside merged child.
def synth_a03b_shared_else_tail(a, b, c, d):
    out = 0
    if a and b > c:
        if not b:
            if c <= d:
                x = 1
            else:
                x = 2
        else:
            x = 3
        out = x + c
    else:
        out = -1
    tail = get_tail(out, a, b, c, d)
    return tail


def get_tail(out, a, b, c, d):
    return out * (a + b + c + d)
