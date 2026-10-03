"""R8-03 Pass in every host position: if arm / loop body / func body / class body / except / else / finally / match."""


def r8_pass_if_arm(x):
    if x > 0:
        pass
    else:
        return -1
    return 0


def r8_pass_loop_body(n):
    for _ in range(n):
        pass
    else:
        pass
    return n


def r8_pass_func():
    pass


class R8PassClass:
    pass


def r8_pass_except(xs, i):
    try:
        return xs[i]
    except IndexError:
        pass
    return None


def r8_pass_while_else(n):
    while n > 0:
        n -= 1
    else:
        pass
    return n


def r8_pass_try_finally():
    try:
        pass
    finally:
        pass
    return 1


def r8_pass_match(x):
    match x:
        case 1:
            pass
        case _:
            pass
    return 2
