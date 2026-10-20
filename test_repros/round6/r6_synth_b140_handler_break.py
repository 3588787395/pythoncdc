def s_b140_handler_break(n):
    total = 0
    while n > 0:
        try:
            n -= 1
        except ValueError:
            break
        total += n
    return total


def s_b140_handler_break_for(items):
    out = []
    for it in items:
        try:
            out.append(it)
        except TypeError:
            break
    return out


def s_b140_handler_continue(items):
    out = []
    for it in items:
        try:
            out.append(it)
        except TypeError:
            continue
    return out
