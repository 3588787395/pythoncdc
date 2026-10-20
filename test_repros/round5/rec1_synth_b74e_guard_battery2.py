"""R5 synth family 1b: guard battery variants (guard + multi-statement body, guard on default, mixed arms)."""


def gb2_guard_body_chain(x, g, sink):
    r = 0
    match x:
        case 1 if g:
            r = 1
            sink.append(r)
            r += 1
        case 2:
            r = 2
        case _ if not g:
            r = -1
    return r


def gb2_nested_guard(x, y, g):
    r = 0
    match x:
        case 5:
            match y:
                case 6 if g:
                    r = 56
                case _:
                    r = 50
        case _:
            r = 9
    return r
