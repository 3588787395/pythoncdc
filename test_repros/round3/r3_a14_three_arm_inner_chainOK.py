# Source Generated with Decompyle++ (Python version)
# File: r3_a14_three_arm_inner_chain.pyc (Python 3.11)

def f(a):
    o = mk(a)
    if o is None:
        return None
    elif not is_trade():
        if o.symbol[:2] in ('11', '12'):
            info = 'CB'
        elif o.symbol[:2] in ('13',):
            info = 'CB2'
        else:
            info = 'STK'
        LOG.info(info)
    else:
        return o.order_id
