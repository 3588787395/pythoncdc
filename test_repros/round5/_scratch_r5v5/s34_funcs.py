def ifwhile(i, flag):
    if flag:
        while i > 0:
            i -= 1
    return i


def ann_bare(x):
    a: int = x + 1
    b: str
    return a, b


def ann_bare_only(x):
    b: str
    return b
