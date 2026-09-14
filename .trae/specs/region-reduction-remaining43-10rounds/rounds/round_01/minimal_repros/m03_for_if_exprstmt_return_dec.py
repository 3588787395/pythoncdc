# Source Generated with Decompyle++ (Python version)
# File: m03_for_if_exprstmt_return.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        if a == 0:
            continue
        msg = 'ok'
        log.info(msg)
        return a
