# Source Generated with Decompyle++ (Python version)
# File: r2_02_try_finally_only.pyc (Python 3.11)

def f(a, b):
    log = []
    try:
        log.append(a)
        if a > b:
            log.append(b)
    finally:
        log.append('end')
    return log
def g(n):
    out = 0
    for i in range(n):
        try:
            if i % 2:
                out += i
        finally:
            out += 1
    return out
