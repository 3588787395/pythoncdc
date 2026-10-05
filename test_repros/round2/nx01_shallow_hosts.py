"""nx01: six hosts at depth 1, shallow equivalent negative control."""
def s_if():
    if 1:
        R = 1
    return 1


def s_for():
    for i in range(1):
        R = i
    return 2


def s_while():
    while 0:
        R = 1
    return 3


def s_try():
    try:
        R = 1
    except ValueError:
        R = 2
    finally:
        F = 3
    return 4


def s_with():
    with _A() as a:
        R = a
    return 5


def s_match():
    match 1:
        case 1:
            R = 1
        case _:
            R = 2
    return 6
