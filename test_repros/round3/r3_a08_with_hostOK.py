# Source Generated with Decompyle++ (Python version)
# File: r3_a08_with_host.pyc (Python 3.11)

def f(a):
    with LOCK as lk:
        o = mk(a)
        if o is None:
            while False:
                pass
        elif not is_trade():
            if o.symbol[:2] in ('11', '12'):
                info = 'CB'
            else:
                info = 'STK'
            LOG.info(info)
        return o.order_id
        return o.order_id
