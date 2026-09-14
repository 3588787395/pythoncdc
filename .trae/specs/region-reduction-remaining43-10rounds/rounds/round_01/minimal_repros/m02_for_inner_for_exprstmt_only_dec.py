# Source Generated with Decompyle++ (Python version)
# File: m02_for_inner_for_exprstmt_only.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        acc = {}
        for b in a:
            acc[b] = 1
        log.info(acc)
        return acc
