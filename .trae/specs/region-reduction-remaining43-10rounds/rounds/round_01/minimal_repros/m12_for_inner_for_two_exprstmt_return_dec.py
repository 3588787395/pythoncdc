# Source Generated with Decompyle++ (Python version)
# File: m12_for_inner_for_two_exprstmt_return.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        for b in a:
            pass
        log.info('one')
        log.info('two')
        return a
