def b2a04_shallow(ks, flag):
    total = 0
    for k in ks:
        if k == 'a':
            total += 1
        elif k == 'b':
            continue
        elif k == 'c':
            total += 3
        total += 100
    return total


def b2a04_deep(ks, flag, mode):
    total = 0
    for k in ks:
        if mode:
            if flag:
                if k == 'a':
                    total += 1
                elif k == 'b':
                    continue
                elif k == 'c':
                    total += 3
            total += 100
        total += 1
    return total
