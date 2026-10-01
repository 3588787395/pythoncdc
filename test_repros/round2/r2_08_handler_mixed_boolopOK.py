# Source Generated with Decompyle++ (Python version)
# File: r2_08_handler_mixed_boolop.pyc (Python 3.11)

def f(a, b, c, log):
    try:
        log.append('body')
    except Exception:
        if a and b or c:
            log.append('t1')
        else:
            log.append('f1')
    log.append('end')
def g(a, b, c, log):
    try:
        log.append('body')
    except Exception:
        if a and b or c:
            log.append('w')
            while False:
                pass
    return log
