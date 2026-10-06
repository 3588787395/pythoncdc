# Source Generated with Decompyle++ (Python version)
# File: r3_a07_try_host.pyc (Python 3.11)

def f(a):
    try:
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
    except ValueError:
        return None
