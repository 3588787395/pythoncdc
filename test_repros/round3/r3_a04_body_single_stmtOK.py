# Source Generated with Decompyle++ (Python version)
# File: r3_a04_body_single_stmt.pyc (Python 3.11)

def f(a):
    o = mk(a)
    if o is None:
        return None
    elif not is_trade():
        LOG.info('x')
    return o.order_id
