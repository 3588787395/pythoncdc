# Source Generated with Decompyle++ (Python version)
# File: m01_for_inner_for_exprstmt_return.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        acc = {}
        for b in a:
            if b == 0:
                continue
            acc[b] = 1
        msg = 'done'
        log.info(msg)
        return acc
