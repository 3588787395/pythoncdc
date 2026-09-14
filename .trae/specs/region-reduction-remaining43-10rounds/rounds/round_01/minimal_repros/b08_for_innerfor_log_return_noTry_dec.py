# Source Generated with Decompyle++ (Python version)
# File: b08_for_innerfor_log_return_noTry.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        for b in a:
            pass
        log.info('x')
        return a
