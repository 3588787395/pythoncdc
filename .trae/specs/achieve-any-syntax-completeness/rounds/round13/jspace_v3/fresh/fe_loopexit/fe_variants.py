def m2(bases):                        # plain for-else + trailing call-assign
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    else:
        boundary = 0
    items = list(bases)
    return boundary, items

def m3(bases):                        # for-else + trailing ternary-assign
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    else:
        boundary = 0
    items = list(bases) if bases else []
    return boundary, items

def m4(bases):                        # for-else + trailing plain assign (no call)
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    else:
        boundary = 0
    items = boundary
    return boundary, items

def m5(bases):                        # no else clause + trailing statements (control)
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    items = list(bases)
    return boundary, items
