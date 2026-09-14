# Source Generated with Decompyle++ (Python version)
# File: m05_for_dictcomp_exprstmt_return.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        acc = {b: b for b in a if b}
        msg = 'ok'
        log.info(msg)
        return {'data': acc}
