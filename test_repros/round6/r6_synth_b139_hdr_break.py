def s_b139_hdr_break(n):
    out = []
    while n > 0:
        if n == 2:
            break
        n -= 1
        out.append(n)
    return out


def s_b139_hdr_break_for(items):
    out = []
    for it in items:
        if it == 'x':
            break
        out.append(it)
    return out
