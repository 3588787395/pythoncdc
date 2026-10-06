# Source Generated with Decompyle++ (Python version)
# File: r3_a10_positive_polarity.pyc (Python 3.11)

def f(a):
    o = mk(a)
    if o is None:
        return None
    elif is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
