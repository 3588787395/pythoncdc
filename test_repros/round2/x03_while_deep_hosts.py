"""x03: While as innermost leaf, host depth >= 3."""
def while_in_if():
    if 1:
        while 1:
            if 1:
                while 1:
                    break
                break
        else:
            R = 1
    return 1


def while_in_for():
    for i in range(1):
        while 1:
            if 1:
                while 1:
                    break
            break
    return 2


def while_in_try():
    try:
        while 1:
            try:
                while 1:
                    break
            finally:
                F = 1
            break
    except ValueError:
        R = 2
    return 3


def while_in_with():
    with _A() as a:
        while 1:
            with _A() as b:
                while 1:
                    break
            break
    return 4


def while_in_match():
    match 1:
        case 1:
            while 1:
                match 1:
                    case 1:
                        while 1:
                            break
                break
    return 5


def while_shallow():
    while 0:
        R = 1
    return 0
