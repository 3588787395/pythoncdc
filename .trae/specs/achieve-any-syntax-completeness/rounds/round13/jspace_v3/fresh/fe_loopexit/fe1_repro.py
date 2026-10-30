def m(bases, abcs=None):
    boundary = -1
    for i, b in enumerate(bases):
        if b == 'A':
            boundary = len(bases) - i
            break
    else:
        boundary = 0
    items = list(abcs) if abcs else []
    extra = boundary + 1
    return boundary, items, extra
