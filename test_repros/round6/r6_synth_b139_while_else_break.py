def s_b139_while_else_break(n):
    out = []
    while n > 0:
        n -= 1
        if n == 3:
            break
    else:
        out.append('done')
    return out


def s_b139_while_else_break2(n):
    out = []
    while n > 0:
        n -= 1
        if n == 2:
            break
        out.append(n)
    else:
        out.append('never')
    return out
