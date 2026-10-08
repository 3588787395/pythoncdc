# Source Generated with Decompyle++ (Python version)
# File: r10g7_06_loopexit_pair_handler_then_loop.pyc (Python 3.11)

def r10g7_06_loopexit_pair_handler_then_loop(x, log, running):
    if x:
        try:
            with CM(x):
                d = g(x)
        except BaseException:
            log.error(d)
        while running:
            k(d)
        return None
    else:
        y = h()
