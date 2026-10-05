"""x04: Try as innermost leaf, host depth >= 3."""
def try_in_if():
    if 1:
        try:
            if 1:
                try:
                    R = 1
                finally:
                    F = 1
        except ValueError:
            R = 2
    return 1


def try_in_for():
    for i in range(1):
        try:
            for j in range(1):
                try:
                    R = j
                except ValueError:
                    R = 0
        finally:
            F = i
    return 2


def try_in_while():
    while 1:
        try:
            while 1:
                try:
                    R = 1
                finally:
                    F = 1
            break
        except ValueError:
            R = 2
    return 3


def try_in_with():
    with _A() as a:
        try:
            with _A() as b:
                try:
                    R = (a, b)
                finally:
                    F = 1
        except ValueError:
            R = 2
    return 4


def try_in_match():
    match 1:
        case 1:
            try:
                match 1:
                    case 1:
                        try:
                            R = 1
                        finally:
                            F = 1
            except ValueError:
                R = 2
    return 5


def try_shallow():
    try:
        R = 1
    except ValueError:
        R = 2
    finally:
        F = 3
    return 0
