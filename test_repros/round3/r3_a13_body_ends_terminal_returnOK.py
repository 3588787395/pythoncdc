# Source Generated with Decompyle++ (Python version)
# File: r3_a13_body_ends_terminal_return.pyc (Python 3.11)

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
