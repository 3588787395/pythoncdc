def r9a1_09_pastconfluence_share_for(q, add, get, lim):
    de_listed = set()
    for o in q:
        i = get(o)
        if i:
            if i.date > lim:
                continue
        add(o)
    return de_listed
