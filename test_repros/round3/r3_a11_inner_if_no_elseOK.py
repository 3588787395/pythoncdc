# Source Generated with Decompyle++ (Python version)
# File: r3_a11_inner_if_no_else.pyc (Python 3.11)

def f(a):
    o = mk(a)
    if o is None:
        return None
    elif not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
    LOG.info(info)
    return o.order_id
