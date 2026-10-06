# Source Generated with Decompyle++ (Python version)
# File: n4_05_neg_except_star.pyc (Python 3.11)

def n_except_star(fn):
    r = None
    try:
        fn()
    except* ValueError as eg:
        r = eg.exceptions
    return r
def n_except_star_two(fn):
    try:
        fn()
    except* ValueError as eg:
        handle(eg)
    else:
        if TypeError is not None:
            pass
        handle(eg)
    return None
