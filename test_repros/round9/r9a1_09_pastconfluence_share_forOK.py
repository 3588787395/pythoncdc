# Source Generated with Decompyle++ (Python version)
# File: r9a1_09_pastconfluence_share_for.pyc (Python 3.11)

def r9a1_09_pastconfluence_share_for(q, add, get, lim):
    de_listed = set()
    for o in q:
        i = get(o)
        if i and i.date > lim:
            continue
        add(o)
        continue
    return de_listed
