def s_b137_while_nop(n):
    out = []
    while True:
        if n > 0:
            n -= 1
            out.append(n)
        else:
            break
    return out


def s_b137_while_nop2(n):
    out = []
    while True:
        if n > 0:
            n -= 1
        else:
            out.append(0)
            break
    return out
