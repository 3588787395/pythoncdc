# Source Generated with Decompyle++ (Python version)
# File: r2_08_handler_mixed_boolop.pyc (Python 3.11)

def f(a, b, c, log):
    try:
        log.append('body')
    except Exception:
        if not (a and b):
            log.append('t1')
        if c:
            pass
        else:
            log.append('f1')
    log.append('end')
def g(a, b, c, log):
    try:
        log.append('body')
    except Exception:
        if not (a and b):
            log.append('w')
            while False:
                pass
        if c:
            pass
    return log
