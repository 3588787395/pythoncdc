# Source Generated with Decompyle++ (Python version)
# File: r3_a12_guard_is_call_not_isnone.pyc (Python 3.11)

def f(a):
    o = mk(a)
    if o.is_bad():
        return None
    elif not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        else:
            info = 'STK'
        LOG.info(info)
    return o.order_id
