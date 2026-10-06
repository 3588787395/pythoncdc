# Source Generated with Decompyle++ (Python version)
# File: r3_a17_negated_if_empty_then_no_fold.pyc (Python 3.11)

def f(a):
    o = mk(a)
    if o is None:
        return None
    elif not is_trade():
        if o.symbol[:2] in ('11', '12'):
            pass
        else:
            LOG.info('skip')
    return o.order_id
