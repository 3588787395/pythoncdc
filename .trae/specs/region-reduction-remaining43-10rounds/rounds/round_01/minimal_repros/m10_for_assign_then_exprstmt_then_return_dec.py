# Source Generated with Decompyle++ (Python version)
# File: m10_for_assign_then_exprstmt_then_return.cpython-311.pyc (Python 3.11)

def f(items):
    for a in items:
        msg = 'hi %s' % a
        log.info(msg)
        return {'error_no': 0, 'error_info': '', 'index': a}
