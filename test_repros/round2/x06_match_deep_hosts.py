"""x06: Match as innermost leaf, host depth >= 3."""
def match_in_if():
    if 1:
        match 1:
            case 1:
                if 1:
                    match 2:
                        case 2:
                            R = 2
    return 1


def match_in_for():
    for i in range(1):
        match i:
            case 0:
                for j in range(1):
                    match j:
                        case 0:
                            R = j
    return 2


def match_in_try():
    try:
        match 1:
            case 1:
                try:
                    match 2:
                        case 2:
                            R = 2
                finally:
                    F = 1
    except ValueError:
        R = 0
    return 3


def match_in_with():
    with _A() as a:
        match 1:
            case 1:
                with _A() as b:
                    match 2:
                        case 2:
                            R = (a, b)
    return 4


def match_in_while():
    while 1:
        match 1:
            case 1:
                while 1:
                    match 2:
                        case 2:
                            R = 2
                    break
        break
    return 5


def match_shallow():
    match 1:
        case 1:
            R = 1
        case _:
            R = 2
    return 0
