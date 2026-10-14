# Source Generated with Decompyle++ (Python version)
# File: r3_a03_ternary_and_format_future_shape.pyc (Python 3.11)

def f(a):
    o = mk(a)
    if o is None:
        return None
    elif not is_trade():
        side = 'BUY' if o.dir.value.upper() == 'BUY' else 'SELL'
        LOG.info('order {0} {1}'.format(o.order_id, side))
    return o.order_id
