def c1_two_tails(seq, d):
    for x in seq:
        if x > 0:
            if x > 10:
                d['a'] = 1
                continue
            d['b'] = 2
        else:
            d['a'] = 3
        d['c'] = 4
    return d


def c2_elif(seq, d):
    for x in seq:
        if x > 0:
            d['a'] = 1
            continue
        elif x < -5:
            d['a'] = 2
        d['c'] = 4
    return d


def c3_break(i, d):
    while i:
        if i == 1 or i == 2:
            d['a'] = 0
            break
        i -= 1
    return d


def c4_inner_continue(seq, d):
    for x in seq:
        for y in x:
            if y == 1 or y == 2:
                d['a'] = 1
                continue
            d['b'] = 2
    return d


def c5_merge_join(seq, d):
    for x in seq:
        if x == 1 or x == 2:
            d['a'] = 0
        else:
            d['a'] = 1
        d['b'] = x
    return d
