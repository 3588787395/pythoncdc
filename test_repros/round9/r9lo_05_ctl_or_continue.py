def r9lo_05_ctl_or_continue(q, k):
    total = 0
    for v in q:
        if v == 1 or k.startswith('_'):
            continue
        total += v
    return total
