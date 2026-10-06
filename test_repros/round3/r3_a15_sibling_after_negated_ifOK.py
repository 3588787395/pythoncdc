# Source Generated with Decompyle++ (Python version)
# File: r3_a15_sibling_after_negated_if.pyc (Python 3.11)

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
    o.used = True
    return o.order_id
