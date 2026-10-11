def or_noguard(x):
    match x:
        case 1 | 2:
            r = 'a'
        case _:
            r = 'b'
    return r


def or_empty_body(x):
    match x:
        case 1 | 2:
            pass
        case _:
            r = 'b'
    return r


def or_strings(x):
    match x:
        case 'p' | 'q':
            r = 'pq'
        case _:
            r = 'zz'
    return r


def or_last_case(x):
    match x:
        case 1:
            r = 'one'
        case 2 | 3:
            r = 'twentyish'
    return r


def or_loop_host(xs):
    for x in xs:
        match x:
            case 1 | 2 if x > 1:
                r = 'small'
            case _:
                r = 'other'
    return r


def or_mid_chain(x):
    match x:
        case 1:
            r = 'one'
        case 2 | 3 | 4:
            r = 'few'
        case 5:
            r = 'five'
        case _:
            r = 'many'
    return r


def or_return_body(x):
    match x:
        case 1 | 2 if x > 1:
            return 'small'
        case _:
            return 'other'
