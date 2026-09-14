# Source Generated with Decompyle++ (Python version)
# File: m06_while_inner_for_exprstmt_return.cpython-311.pyc (Python 3.11)

def f(items):
    if items:
        a = items.pop()
        for b in a:
            if b < 0:
                continue
        log.info('x')
        return a
