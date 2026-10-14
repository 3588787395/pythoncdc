# Source Generated with Decompyle++ (Python version)
# File: r8b121_03_if_then_return_in_loop.pyc (Python 3.11)

def b121_03(q, log, ex):
    while True:
        try:
            d = q.get(5)
            if d == SENTINEL:
                return None
            else:
                touch(d)
        except BaseException as e:
            if log:
                log.err(e)
            if STOP:
                return None
