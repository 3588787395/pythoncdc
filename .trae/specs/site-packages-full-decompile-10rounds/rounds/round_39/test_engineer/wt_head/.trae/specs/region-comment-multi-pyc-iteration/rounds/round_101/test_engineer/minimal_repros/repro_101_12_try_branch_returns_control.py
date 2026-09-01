# R101 control: try + if/else where each branch returns its own value
# (no shared tail) - historically healthy shape.


def clamp(v, lo, hi):
    try:
        if v < lo:
            return lo
        else:
            return hi
    except BaseException as x:
        raise x


def run(v, lo, hi):
    return clamp(v, lo, hi)
