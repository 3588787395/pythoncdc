# Source Generated with Decompyle++ (Python version)
# File: r2v3_a20_or_isnone_inside_try.pyc (Python 3.11)

def f(a, b, c):
    try:
        if not a is not None or b is None:
            return c
        else:
            use(a)
    except ValueError:
        log('e')
    return c
