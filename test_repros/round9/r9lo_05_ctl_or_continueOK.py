# Source Generated with Decompyle++ (Python version)
# File: r9lo_05_ctl_or_continue.pyc (Python 3.11)

def r9lo_05_ctl_or_continue(q, k):
    total = 0
    for v in q:
        if v == 1 or k.startswith('_'):
            continue
        total += v
        continue
    return total
