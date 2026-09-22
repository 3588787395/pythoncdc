def s1_plain(seq, d):
    for x in seq:
        if x > 0:
            d['a'] = 1
        else:
            d['a'] = 2
    return d


def s2_or(seq, d):
    for x in seq:
        if x == 1 or x == 2:
            d['a'] = 0
        else:
            d['a'] = 1
    return d


def s3_cont(seq, d):
    for x in seq:
        if x > 0:
            d['a'] = 1
            continue
        d['a'] = 2
    return d


def s4_noelse(seq, d):
    for x in seq:
        if x > 0:
            d['a'] = 1
        d['b'] = 2
    return d


def s5_and(seq, d):
    for x in seq:
        if x > 0 and x < 5:
            d['a'] = 0
        else:
            d['a'] = 1
    return d


def s6_while(a, d):
    i = 0
    while i < a:
        if i == 1 or i == 2:
            d['a'] = 0
        else:
            d['a'] = 1
        i += 1
    return d


def s7_nested(seq, d):
    for x in seq:
        for y in x:
            if y == 1 or y == 2:
                d['a'] = 0
            else:
                d['a'] = 1
    return d
