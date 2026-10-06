def b2b03_shallow(ks, flag):
    n = 0
    for k in ks:
        if k != 'x':
            if k == 'y':
                continue
            n += 1
    return n


def b2b03_deep(ks, flag):
    n = 0
    for k in ks:
        if flag:
            if k != 'x':
                if k == 'y':
                    continue
                n += 1
    return n
