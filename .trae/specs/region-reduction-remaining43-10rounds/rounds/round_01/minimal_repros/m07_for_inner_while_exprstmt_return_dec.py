# Source Generated with Decompyle++ (Python version)
# File: m07_for_inner_while_exprstmt_return.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        n = 0
        while n < 3:
            n += 1
        log.info(n)
        return n
