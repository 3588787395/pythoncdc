# R101-Pattern-A-variant: try + if/elif/else + shared return False


def check(v, lim):
    try:
        if v < 0:
            v = -v
        elif v > lim:
            v = lim
        else:
            v = 0
        return False
    except BaseException as x:
        raise x


def run(v, lim):
    return check(v, lim)
